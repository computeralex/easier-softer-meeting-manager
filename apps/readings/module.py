"""
Readings module registration.
"""
from apps.registry.base_module import BaseModule, ModuleConfig, NavItem, SettingsSection


class ReadingsModule(BaseModule):
    """
    Readings module for managing meeting readings, prayers, and texts.
    Secretary or GSR can manage.
    """

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='readings',
            verbose_name='Readings',
            description='Manage meeting readings, prayers, and texts',
            version='1.0.0',
            url_prefix='readings',
            required_positions=['secretary', 'group_rep'],  # Who can edit
            read_positions=[],  # All can read
            icon='book',
            order=35,  # Before Meeting Format
            settings_url=None,  # Settings in Global Settings only
            nav_items=[
                NavItem(
                    label='Readings',
                    url_name='readings:list',
                    icon='book',
                    order=35,
                    namespace='readings',
                ),
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from .models import Reading, ReadingCategory
        from apps.treasurer.models import Meeting

        meeting = Meeting.objects.first()
        if not meeting:
            return []

        reading_count = Reading.objects.filter(meeting=meeting, is_active=True).count()
        category_count = ReadingCategory.objects.filter(meeting=meeting, is_active=True).count()

        return [{
            'template': 'readings/widgets/summary.html',
            'context': {
                'reading_count': reading_count,
                'category_count': category_count,
            },
            'order': 35,
        }]

    def get_settings_sections(self, request):
        """Return settings sections for global settings page."""
        return [
            SettingsSection(
                name='readings',
                title='Readings',
                template='readings/settings_section.html',
                icon='book',
                order=35,
                description='Manage readings sharing settings',
            )
        ]

    def get_settings_context(self, request, section_name):
        """Return context for the readings settings section."""
        from .models import ReadingsModuleConfig
        from apps.treasurer.models import Meeting

        meeting, _ = Meeting.objects.get_or_create(pk=1, defaults={'name': 'My Meeting'})
        config, _ = ReadingsModuleConfig.objects.get_or_create(meeting=meeting)

        return {
            'config': config,
            'meeting': meeting,
            'public_url': request.build_absolute_uri('/readings/'),
        }
