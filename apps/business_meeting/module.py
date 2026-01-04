"""
Business Meeting module registration.
Manages business meeting format and notes/minutes.
"""
from apps.registry.base_module import BaseModule, ModuleConfig, NavItem


class BusinessMeetingModule(BaseModule):
    """
    Business Meeting module for managing business meeting format and notes.
    """

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='business_meeting',
            verbose_name='Business Meeting',
            description='Manage business meeting format and notes',
            version='1.0.0',
            url_prefix='business',
            required_positions=['secretary', 'group_rep'],
            read_positions=[],  # All authenticated can read
            icon='clipboard-check',
            order=45,
            settings_url=None,
            nav_items=[
                NavItem(
                    label='Business',
                    url_name='business_meeting:meeting_list',
                    icon='clipboard-check',
                    order=45,
                    namespace='business_meeting',
                )
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from .models import BusinessMeeting
        from apps.treasurer.models import Meeting

        meeting = Meeting.objects.first()
        if not meeting:
            return []

        meetings = BusinessMeeting.objects.filter(meeting=meeting)
        meeting_count = meetings.count()
        last_meeting = meetings.first()  # Already ordered by -date

        return [{
            'template': 'business_meeting/widgets/summary.html',
            'context': {
                'meeting_count': meeting_count,
                'last_meeting': last_meeting,
            },
            'order': 45,
        }]
