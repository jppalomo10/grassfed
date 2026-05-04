import threading

_thread_locals = threading.local()

# Apps whose models live in the default MySQL DB (Django internals)
_DJANGO_APPS = {'auth', 'admin', 'sessions', 'contenttypes', 'messages'}


class ERPDatabaseRouter:
    """
    Routes ERP models to the MySQL connection that matches the logged-in
    user's role (set by DatabaseRoleMiddleware). Django's own tables always
    go to 'default' (MySQL) and are never migrated via ERP aliases.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label in _DJANGO_APPS:
            return 'default'
        return getattr(_thread_locals, 'db_alias', 'default')

    def db_for_write(self, model, **hints):
        if model._meta.app_label in _DJANGO_APPS:
            return 'default'
        return getattr(_thread_locals, 'db_alias', 'default')

    def allow_relation(self, _obj1, _obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **_hints):
        # Only Django's own apps migrate to 'default'; ERP tables are managed=False
        if app_label in _DJANGO_APPS:
            return db == 'default'
        return False
