"""
Django development settings.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'meeting.local']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email - console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
