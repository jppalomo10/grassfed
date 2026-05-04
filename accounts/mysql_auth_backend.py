"""
Custom Django authentication backend that validates credentials directly
against MySQL.

Flow:
  1. User submits username + password on the Django login form.
  2. This backend opens a **temporary** MySQL connection using those
     credentials.
  3. If MySQL accepts the connection → the user is legit.
  4. We run ``SELECT CURRENT_ROLE()`` to detect the MySQL role.
  5. A Django ``User`` is created / updated automatically with the
     matching Django group (dev, admin, usuario).
  6. The existing ``DatabaseRoleMiddleware`` then picks the right DB
     alias for all subsequent ERP queries.

This means:
  • Adding a new MySQL user + role is enough — they can log into Django
    immediately without touching ``.env`` or running management commands.
  • The ``.env`` database connections (dev / admin / erp_user) still
    represent the **three roles**, not individual people.
"""

import logging

import MySQLdb
from django.conf import settings
from django.contrib.auth.models import Group, User

logger = logging.getLogger(__name__)

# MySQL role name  →  Django group name
_ROLE_TO_GROUP = {
    'dev_role': 'dev',
    'admin_role': 'admin',
    'user_role': 'usuario',
}


class MySQLAuthBackend:
    """Authenticate a user by attempting a real MySQL connection."""

    # ------------------------------------------------------------------
    # authenticate()
    # ------------------------------------------------------------------
    def authenticate(self, request, username=None, password=None):
        if not username or not password:
            return None

        # Grab host / port / db from any existing MySQL config
        db_conf = settings.DATABASES.get('dev', {})
        host = db_conf.get('HOST', 'localhost')
        port = int(db_conf.get('PORT', 3306))
        db_name = db_conf.get('NAME', 'grassfed_erp')

        # --- 1. Try to connect to MySQL with the supplied credentials ---
        try:
            conn = MySQLdb.connect(
                host=host,
                port=port,
                user=username,
                passwd=password,
                db=db_name,
                charset='utf8mb4',
            )
        except MySQLdb.Error:
            # Bad credentials or user doesn't exist → let Django try next
            return None

        # --- 2. Detect the active MySQL role ---
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT CURRENT_ROLE()")
                row = cur.fetchone()
                role_raw = row[0] if row else 'NONE'
        except MySQLdb.Error:
            role_raw = 'NONE'
        finally:
            conn.close()

        django_group_name = self._parse_role(role_raw)
        if django_group_name is None:
            logger.warning(
                "MySQL user '%s' authenticated but has no recognised role "
                "(%s). Login denied.",
                username,
                role_raw,
            )
            return None

        # --- 3. Get or create the Django user & assign the group ---
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'is_active': True},
        )
        if created:
            # Set an unusable password — auth always goes through MySQL
            user.set_unusable_password()
            user.save()
            logger.info("Auto-created Django user '%s'.", username)

        group, _ = Group.objects.get_or_create(name=django_group_name)
        if set(user.groups.values_list('name', flat=True)) != {django_group_name}:
            user.groups.set([group])
            logger.info(
                "User '%s' assigned to group '%s'.", username, django_group_name
            )

        return user

    # ------------------------------------------------------------------
    # get_user()  (required by the auth backend API)
    # ------------------------------------------------------------------
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_role(role_raw: str) -> str | None:
        """
        Parse the string returned by ``SELECT CURRENT_ROLE()``.

        MySQL 8.0 returns formats like:
          ``NONE``
          ``\`dev_role\`@\`%\```
          ``\`dev_role\`@\`%\`,\`admin_role\`@\`%\```  (multiple roles)

        We return the **first** recognised Django group name, or *None*.
        """
        if not role_raw or role_raw.upper() == 'NONE':
            return None
        for mysql_role, group_name in _ROLE_TO_GROUP.items():
            if mysql_role in role_raw:
                return group_name
        return None
