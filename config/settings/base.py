"""
Django base settings for Meeting Manager.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'django_htmx',
    'csp',  # django-csp for Content Security Policy
    'axes',  # Brute force login protection

    # Project apps - order matters for migrations
    'apps.core',
    'apps.registry',
    'apps.positions',
    'apps.treasurer',
    'apps.phone_list',
    'apps.readings',
    'apps.meeting_format',
    'apps.business_meeting',
    'apps.website',
]

# Custom user model
AUTH_USER_MODEL = 'core.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',  # Content Security Policy headers
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'apps.core.middleware.SetupWizardMiddleware',  # Setup wizard redirect
    'axes.middleware.AxesMiddleware',  # Brute force protection (must be last)
]

# Authentication backends (axes must be first)
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors
                'apps.core.context_processors.navigation',
                'apps.core.context_processors.meeting_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Los_Angeles'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Authentication
LOGIN_URL = 'website:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'website:home'

# Email Configuration
# Console backend by default (prints to terminal). Set env vars for SMTP.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@meetingmanager.local')

# Module registry - apps to autodiscover
MEETING_MODULES = [
    'apps.positions',
    'apps.treasurer',
    'apps.phone_list',
    'apps.readings',
    'apps.meeting_format',
    'apps.business_meeting',
    'apps.website',
    # 'apps.secretary',
    # 'apps.announcements',
]

# Content Security Policy (CSP) - Base settings for development
# Production settings in production.py are more strict
# Using django-csp 4.0+ format
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'"),  # Allow inline for dev
        'style-src': ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"),
        'img-src': ("'self'", "data:", "https:"),
        'font-src': ("'self'", "https://cdn.jsdelivr.net", "https://fonts.gstatic.com"),
        'connect-src': ("'self'",),
        'frame-src': ("https://www.youtube.com", "https://www.youtube-nocookie.com",
                      "https://player.vimeo.com"),
        'frame-ancestors': ("'self'",),
    }
}

# Django Axes - Brute force login protection
AXES_FAILURE_LIMIT = 10  # Lock after 10 failed attempts
AXES_COOLOFF_TIME = 0.5  # Lock for 30 minutes (0.5 hours)
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']  # Track by both
AXES_RESET_ON_SUCCESS = True  # Reset failed count on successful login
AXES_ENABLE_ADMIN = True  # Show axes info in admin
