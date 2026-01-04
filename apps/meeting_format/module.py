"""
Meeting Format module registration.
"""
from apps.registry.base_module import BaseModule, ModuleConfig, NavItem, SettingsSection


class MeetingFormatModule(BaseModule):
    """Meeting Format module for managing meeting scripts and rotating formats."""

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='meeting_format',
            verbose_name='Meeting Format',
            description='Manage meeting scripts and rotating formats',
            version='1.0.0',
            url_prefix='format',
            required_positions=['secretary', 'group_rep'],
            read_positions=[],
            icon='card-text',
            order=40,
            settings_url=None,
            nav_items=[
                NavItem(
                    label='Format',
                    url_name='meeting_format:block_list',
                    icon='card-text',
                    order=40,
                    namespace='meeting_format',
                )
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from .models import FormatBlock, FormatModuleConfig
        from apps.treasurer.models import Meeting

        meeting = Meeting.objects.first()
        if not meeting:
            return []

        block_count = FormatBlock.objects.filter(meeting=meeting, is_active=True).count()

        return [{
            'template': 'meeting_format/widgets/summary.html',
            'context': {
                'block_count': block_count,
            },
            'order': 40,
        }]

    def get_settings_sections(self, request):
        """Return settings sections for global settings page."""
        return [
            SettingsSection(
                name='meeting_format',
                title='Meeting Format',
                template='meeting_format/settings_section.html',
                icon='card-text',
                order=40,
                description='Manage meeting format sharing settings',
            )
        ]

    def get_settings_context(self, request, section_name):
        """Return context for the meeting format settings section."""
        from .models import FormatModuleConfig, FormatBlock
        from apps.treasurer.models import Meeting

        meeting, _ = Meeting.objects.get_or_create(pk=1, defaults={'name': 'Easier Softer Group'})
        config, _ = FormatModuleConfig.objects.get_or_create(meeting=meeting)
        block_count = FormatBlock.objects.filter(meeting=meeting, is_active=True).count()

        return {
            'format_config': config,
            'block_count': block_count,
            'meeting': meeting,
        }
