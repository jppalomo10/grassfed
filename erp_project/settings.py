from pathlib import Path
import environ
from django.contrib.messages import constants as msg_constants

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='dev-secret-key-change-in-production-please')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'accounts',
    'dashboard',
    'clientes',
    'productos',
    'pedidos',
    'reportes',
    'dev',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.DatabaseRoleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_group',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_project.wsgi.application'

# --- Databases ---
# 'default' → MySQL jppalomo10 (Django internal tables + superuser fallback)
# Dynamic per-user aliases are created at runtime by DatabaseRoleMiddleware.

_MYSQL_BASE = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': env('DB_NAME', default='grassfed_erp'),
    'USER': env('DB_DEV_USER', default='jppalomo10'),
    'PASSWORD': env('DB_DEV_PASSWORD', default=''),
    'HOST': env('DB_HOST', default='localhost'),
    'PORT': env('DB_PORT', default='3306'),
    'OPTIONS': {
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_ALL_TABLES'",
    },
}

DATABASES = {
    'default': _MYSQL_BASE,
}

DATABASE_ROUTERS = ['core.db_router.ERPDatabaseRouter']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Authentication: validate against MySQL first, Django DB as fallback (superuser only)
AUTHENTICATION_BACKENDS = [
    'accounts.mysql_auth_backend.MySQLAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = 'es-gt'
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Suppress intentional composite-PK workaround warning on DetallePedido
SILENCED_SYSTEM_CHECKS = ['fields.W342']

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

MESSAGE_TAGS = {
    msg_constants.DEBUG: 'secondary',
    msg_constants.INFO: 'info',
    msg_constants.SUCCESS: 'success',
    msg_constants.WARNING: 'warning',
    msg_constants.ERROR: 'danger',
}
