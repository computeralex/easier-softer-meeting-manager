from django.apps import AppConfig


class RegistryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.registry'
    verbose_name = 'Module Registry'

    def ready(self):
        """Discover and register all modules when Django starts."""
        from .module_registry import registry
        registry.autodiscover()
