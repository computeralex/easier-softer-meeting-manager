"""
Context processors for global template variables.
"""
from .models import MeetingConfig


def navigation(request):
    """
    Add navigation items to all templates.
    Navigation is built dynamically from registered modules.
    """
    if not request.user.is_authenticated:
        return {'nav_items': [], 'accessible_modules': []}

    # Import here to avoid circular imports
    from apps.registry.module_registry import registry

    return {
        'nav_items': registry.get_navigation_for_user(request),
        'accessible_modules': [
            m.config for m in registry.get_modules_for_user(request.user)
        ],
    }


def meeting_config(request):
    """Add meeting configuration to all templates."""
    return {
        'meeting_config': MeetingConfig.get_instance(),
    }
