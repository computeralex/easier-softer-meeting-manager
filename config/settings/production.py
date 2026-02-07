"""
Django production settings.
"""
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from .base import *

DEBUG = False

# SECRET_KEY is required in production - no default allowed
if not os.environ.get('SECRET_KEY'):
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable is required in production. "
        "Generate one with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    )
SECRET_KEY = os.environ['SECRET_KEY']

# Allowed hosts - support Railway's dynamic domains
_hosts = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()]
RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

# CSRF trusted origins for Railway
CSRF_TRUSTED_ORIGINS = []
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RAILWAY_PUBLIC_DOMAIN}')
# Add any custom domains
custom_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if custom_origins:
    CSRF_TRUSTED_ORIGINS.extend(custom_origins.split(','))

# Database - PostgreSQL for production
# Supports DATABASE_URL (Railway) or individual DB_* vars
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'meeting_manager'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Static files with WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Trust Railway's proxy - required to avoid redirect loops
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS - Force HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True

# Additional security headers
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Logging - capture errors to console (visible in Railway logs)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Content Security Policy via django-csp (4.0+ format)
# Note: 'unsafe-inline' for scripts is needed until inline JS is refactored to external files
# TODO: Remove 'unsafe-inline' from script-src after refactoring inline JS
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://unpkg.com"),  # TODO: Remove 'unsafe-inline' after JS refactor
        'style-src': ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"),
        'img-src': ("'self'", "data:", "https:"),
        'font-src': ("'self'", "https://cdn.jsdelivr.net", "https://fonts.gstatic.com"),
        'connect-src': ("'self'",),
        'frame-src': ("https://www.youtube.com", "https://www.youtube-nocookie.com",
                      "https://player.vimeo.com"),  # Allowed embed sources
        'frame-ancestors': ("'none'",),  # Prevent clickjacking
    }
}
