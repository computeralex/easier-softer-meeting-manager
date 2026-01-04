"""
Phone List app configuration.
"""
from django.apps import AppConfig


class PhoneListConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.phone_list'
    verbose_name = 'Phone List'
