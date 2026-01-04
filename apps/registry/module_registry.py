"""
Central module registry that discovers and manages all modules.
Similar to WordPress hooks system and Django admin registry.
"""
import importlib
import logging
from typing import Dict, List, Optional, Type

from django.conf import settings

from .base_module import BaseModule

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Singleton registry for all application modules.
    Handles discovery, registration, and access control.
    """

    _instance = None
    _modules: Dict[str, BaseModule] = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, module_class: Type[BaseModule]) -> None:
        """
        Register a module with the registry.

        Args:
            module_class: The module class to register
        """
        module = module_class()
        name = module.config.name

        if name in self._modules:
            logger.warning(f"Module '{name}' already registered, skipping.")
            return

        self._modules[name] = module
        module.on_register()
        logger.info(f"Registered module: {name} (v{module.config.version})")

    def autodiscover(self) -> None:
        """
        Automatically discover and register all modules.
        Looks for 'module.py' in each installed app.
        Similar to Django admin's autodiscover_modules.
        """
        if self._initialized:
            return

        # Get list of module apps from settings
        module_apps = getattr(settings, 'MEETING_MODULES', [])

        for app_name in module_apps:
            try:
                module_path = f"{app_name}.module"
                module = importlib.import_module(module_path)

                # Look for a class that inherits from BaseModule
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BaseModule) and
                        attr is not BaseModule):
                        self.register(attr)
                        break

            except ImportError as e:
                # Module doesn't have a module.py file, skip it
                logger.debug(f"No module registration found for {app_name}: {e}")
            except Exception as e:
                logger.error(f"Error loading module {app_name}: {e}")

        self._initialized = True

        # Call on_ready for all modules
        for module in self._modules.values():
            module.on_ready()

    def get_module(self, name: str) -> Optional[BaseModule]:
        """Get a specific module by name."""
        return self._modules.get(name)

    def get_all_modules(self) -> Dict[str, BaseModule]:
        """Get all registered modules."""
        return self._modules.copy()

    def get_enabled_modules(self) -> Dict[str, BaseModule]:
        """Get only enabled modules."""
        return {
            name: module
            for name, module in self._modules.items()
            if module.config.is_enabled
        }

    def get_modules_for_user(self, user) -> List[BaseModule]:
        """
        Get modules accessible to a specific user based on their positions.

        Args:
            user: The user to check access for

        Returns:
            List of modules the user can access, sorted by order
        """
        accessible = []
        for module in self._modules.values():
            if module.config.is_enabled and module.check_access(user):
                accessible.append(module)

        return sorted(accessible, key=lambda m: m.config.order)

    def get_navigation_for_user(self, request) -> List[Dict]:
        """
        Build the complete navigation structure for a user.

        Args:
            request: The HTTP request (contains user)

        Returns:
            List of navigation items with module info
        """
        nav_items = []

        for module in self.get_modules_for_user(request.user):
            module_nav = module.get_nav_items(request)
            for item in module_nav:
                nav_items.append({
                    'module': module.config.name,
                    'label': item.label,
                    'url_name': item.url_name,
                    'icon': item.icon,
                    'order': item.order,
                    'badge': item.badge,
                    'children': item.children,
                    'namespace': item.namespace,
                })

        return sorted(nav_items, key=lambda x: x['order'])

    def get_settings_sections_for_user(self, request) -> List[Dict]:
        """
        Get all settings sections from all accessible modules.

        Args:
            request: The HTTP request (contains user)

        Returns:
            List of settings section dicts with module info
        """
        sections = []

        for module in self.get_modules_for_user(request.user):
            # Only include settings from modules user can write to
            if not module.check_write_access(request.user):
                continue

            module_sections = module.get_settings_sections(request)
            for section in module_sections:
                context = module.get_settings_context(request, section.name)
                sections.append({
                    'module': module,
                    'module_name': module.config.name,
                    'module_verbose_name': module.config.verbose_name,
                    'name': section.name,
                    'title': section.title,
                    'template': section.template,
                    'icon': section.icon or module.config.icon,
                    'order': section.order,
                    'description': section.description,
                    'context': context,
                })

        return sorted(sections, key=lambda x: x['order'])


# Global registry instance
registry = ModuleRegistry()


def register_module(module_class: Type[BaseModule]) -> Type[BaseModule]:
    """
    Decorator to register a module class.

    Usage:
        @register_module
        class TreasurerModule(BaseModule):
            ...
    """
    registry.register(module_class)
    return module_class
