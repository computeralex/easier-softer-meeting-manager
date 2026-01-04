"""
Settings module - defaults to development.
Use DJANGO_SETTINGS_MODULE env var to switch.
"""
import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
