"""
Phone List module registration.
"""
from django.db import models

from apps.registry.base_module import BaseModule, ModuleConfig, NavItem, SettingsSection


class PhoneListModule(BaseModule):
    """
    Phone List module for contact directory.
    Any service position holder can manage.
    """

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='phone_list',
            verbose_name='Phone List',
            description='Contact directory for meeting members',
            version='1.0.0',
            url_prefix='phone-list',
            required_positions=[],  # Any service position can manage
            read_positions=[],  # Any authenticated user can read
            icon='telephone',
            order=20,
            settings_url=None,  # Settings in Global Settings only
            nav_items=[
                NavItem(
                    label='Phone List',
                    url_name='phone_list:list',
                    icon='telephone',
                    order=20,
                    namespace='phone_list',
                ),
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from .models import Contact
        from apps.treasurer.models import Meeting

        meeting = Meeting.objects.first()
        if not meeting:
            return []

        total_count = Contact.objects.filter(meeting=meeting).count()
        active_count = Contact.objects.filter(meeting=meeting, is_active=True).count()

        return [{
            'template': 'phone_list/widgets/summary.html',
            'context': {
                'contact_count': total_count,
                'active_count': active_count,
            },
            'order': 20,
        }]

    def get_settings_sections(self, request):
        """Return settings sections for global settings page."""
        return [
            SettingsSection(
                name='phone_list',
                title='Phone List',
                template='phone_list/settings_section.html',
                icon='telephone',
                order=20,
                description='Manage phone list sharing and time zones',
            )
        ]

    def get_settings_context(self, request, section_name):
        """Return context for the phone list settings section."""
        from .models import PhoneListConfig, TimeZone
        from apps.treasurer.models import Meeting
        from apps.core.models import MeetingConfig

        meeting, _ = Meeting.objects.get_or_create(pk=1, defaults={'name': 'My Meeting'})
        config, _ = PhoneListConfig.objects.get_or_create(meeting=meeting)

        time_zones = TimeZone.objects.filter(
            models.Q(meeting=meeting) | models.Q(meeting__isnull=True),
            is_active=True
        )

        return {
            'config': config,
            'meeting': meeting,
            'time_zones': time_zones,
            'public_url': request.build_absolute_uri(f'/p/{config.share_token}/'),
            'sobriety_term': MeetingConfig.get_instance().get_sobriety_term_label(),
        }
