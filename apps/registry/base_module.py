"""
Base module class that all service position modules must inherit from.
Similar to WordPress plugin registration pattern.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class NavItem:
    """Navigation item configuration."""
    label: str
    url_name: str
    icon: str = ""
    order: int = 100
    badge: Optional[str] = None  # Dynamic badge like count
    namespace: str = ""  # URL namespace for active state detection
    children: List['NavItem'] = field(default_factory=list)


@dataclass
class SettingsSection:
    """Settings section that appears in Global Settings."""
    name: str  # Unique identifier
    title: str  # Display title
    template: str  # Template path to include
    icon: str = ""
    order: int = 100
    description: str = ""


@dataclass
class ModuleConfig:
    """Module configuration."""
    name: str
    verbose_name: str
    description: str = ""
    version: str = "1.0.0"
    url_prefix: str = ""
    # Positions that can write/modify
    required_positions: List[str] = field(default_factory=list)
    # Positions that can read (empty = all authenticated users)
    read_positions: List[str] = field(default_factory=list)
    nav_items: List[NavItem] = field(default_factory=list)
    settings_url: Optional[str] = None
    icon: str = ""
    order: int = 100  # Navigation order
    is_enabled: bool = True


class BaseModule(ABC):
    """
    Abstract base class for all pluggable modules.

    Each module must implement this to register with the system.
    Inspired by Django admin's autodiscover pattern.
    """

    @property
    @abstractmethod
    def config(self) -> ModuleConfig:
        """Return the module configuration."""
        pass

    def get_nav_items(self, request) -> List[NavItem]:
        """
        Return navigation items for this module.
        Override to add dynamic badges or conditional items.
        """
        return self.config.nav_items

    def check_access(self, user) -> bool:
        """
        Check if user has access to view this module.
        By default, any service position holder can view.
        """
        if not self.config.read_positions:
            # No restriction - any authenticated user
            return True
        return user.has_any_position(self.config.read_positions)

    def check_write_access(self, user) -> bool:
        """
        Check if user can modify data in this module.
        """
        if not self.config.required_positions:
            return True
        return user.has_any_position(self.config.required_positions)

    def get_dashboard_widgets(self, request) -> List[Dict[str, Any]]:
        """
        Return dashboard widgets for this module.
        Override to add module-specific dashboard content.
        """
        return []

    def get_settings_sections(self, request) -> List[SettingsSection]:
        """
        Return settings sections for the global settings page.
        Override to add module-specific settings sections.

        Each section should have a template that renders the settings UI.
        The template will receive 'request' and 'module' in context.
        """
        return []

    def get_settings_context(self, request, section_name: str) -> Dict[str, Any]:
        """
        Return additional context for a settings section template.
        Override to provide section-specific data.

        Args:
            request: The HTTP request
            section_name: The name of the section being rendered
        """
        return {}

    def handle_settings_post(self, request, section_name: str) -> Optional[str]:
        """
        Handle POST request for a settings section.
        Override to process form submissions.

        Args:
            request: The HTTP request with POST data
            section_name: The name of the section being posted to

        Returns:
            Optional success message, or None if not handled
        """
        return None

    def on_register(self):
        """Hook called when module is registered. Override for setup tasks."""
        pass

    def on_ready(self):
        """Hook called when Django is ready. Override for initialization."""
        pass
