"""
Positions module registration.
Manages service positions and assignments.
"""
from apps.registry.base_module import BaseModule, ModuleConfig, NavItem, SettingsSection


class PositionsModule(BaseModule):
    """
    Service Positions module for managing positions and assignments.
    Users with can_manage_users=True on their position can access.
    """

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='positions',
            verbose_name='Service Positions',
            description='Manage service positions and assignments',
            version='1.0.0',
            url_prefix='positions',
            required_positions=['treasurer', 'secretary'],  # Write access
            read_positions=[],  # All can read position directory
            icon='person-badge',
            order=15,  # After dashboard, before modules
            settings_url=None,
            nav_items=[
                NavItem(
                    label='Service',
                    url_name='positions:list',
                    icon='person-badge',
                    order=15,
                    namespace='positions',
                ),
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from apps.core.models import ServicePosition, PositionAssignment

        positions = ServicePosition.objects.filter(is_active=True)
        # Available = no primary holder (still needs someone dedicated)
        available_count = sum(1 for p in positions if p.is_available())
        # Vacant = no holders at all
        vacant_count = sum(1 for p in positions if p.get_holder_count() == 0)

        expiring_soon = PositionAssignment.objects.filter(
            end_date__isnull=True
        ).select_related('position', 'user')

        # Count positions with terms ending soon
        expiring_count = sum(1 for a in expiring_soon if a.is_term_ending_soon)

        return [{
            'template': 'positions/widgets/summary.html',
            'context': {
                'position_count': positions.count(),
                'available_count': available_count,
                'vacant_count': vacant_count,
                'expiring_count': expiring_count,
            },
            'order': 15,
        }]

    def get_settings_sections(self, request):
        """Return settings sections for global settings page."""
        return [
            SettingsSection(
                name='positions',
                title='Service',
                template='positions/settings_section.html',
                icon='person-badge',
                order=15,
                description='Configure service position settings',
            )
        ]

    def get_settings_context(self, request, section_name):
        """Return context for the positions settings section."""
        from apps.core.models import ServicePosition, MeetingConfig

        config = MeetingConfig.get_instance()
        return {
            'positions': ServicePosition.objects.filter(is_active=True).order_by('display_name'),
            'meeting_config': config,
            'display_choices': MeetingConfig.PUBLIC_OFFICERS_DISPLAY_CHOICES,
        }

    def handle_settings_post(self, request, section_name):
        """Handle POST for positions settings section."""
        from apps.core.models import MeetingConfig

        public_display = request.POST.get('public_officers_display')
        if public_display:
            config = MeetingConfig.get_instance()
            config.public_officers_display = public_display
            config.save(update_fields=['public_officers_display'])
        return None
