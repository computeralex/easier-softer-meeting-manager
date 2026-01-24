"""
Django development settings.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed (production), skip .env loading

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

# Email - use .env settings if configured, otherwise console backend
if not os.environ.get('EMAIL_HOST_PASSWORD'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
