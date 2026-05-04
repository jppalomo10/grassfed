import threading

from django.conf import settings
from django.db import connections

from core.db_router import _thread_locals

_lock = threading.Lock()


class DatabaseRoleMiddleware:
    """
    Creates a dynamic MySQL connection per user using the credentials stored
    in the session during login. Superusers fall back to 'default'.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            mysql_user = request.session.get('mysql_user')
            mysql_pass = request.session.get('mysql_password')

            if mysql_user and mysql_pass:
                alias = f'erp_{mysql_user}'
                with _lock:
                    if alias not in connections.databases:
                        base = settings.DATABASES['default']
                        connections.databases[alias] = {
                            'ENGINE': 'django.db.backends.mysql',
                            'NAME': base['NAME'],
                            'USER': mysql_user,
                            'PASSWORD': mysql_pass,
                            'HOST': base['HOST'],
                            'PORT': base['PORT'],
                            'OPTIONS': base.get('OPTIONS', {}),
                            'ATOMIC_REQUESTS': False,
                            'AUTOCOMMIT': True,
                            'CONN_MAX_AGE': 0,
                            'CONN_HEALTH_CHECKS': False,
                            'TIME_ZONE': None,
                            'TEST': {},
                        }
                _thread_locals.db_alias = alias
            else:
                # Superuser logged in via Django admin (no MySQL session creds)
                _thread_locals.db_alias = 'default'
        else:
            _thread_locals.db_alias = 'default'

        response = self.get_response(request)
        return response
