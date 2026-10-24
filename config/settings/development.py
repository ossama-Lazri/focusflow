from decouple import config
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '::1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

INTERNAL_IPS = ['127.0.0.1']

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-do-not-use-in-production-abc123xyz')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
