"""
Treasurer module registration.
Defines how this module integrates with the system.
"""
from apps.registry.base_module import BaseModule, ModuleConfig, NavItem, SettingsSection


class TreasurerModule(BaseModule):
    """
    Treasurer module for financial management.
    Only users with treasurer position can modify data.
    All service position holders can view.
    """

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='treasurer',
            verbose_name='Treasury',
            description='Financial management for meeting treasurers',
            version='1.0.0',
            url_prefix='treasurer',
            required_positions=['treasurer'],  # Write access
            read_positions=[],  # Empty = all authenticated users can read
            icon='currency-dollar',
            order=30,
            settings_url=None,  # Settings in Global Settings only
            nav_items=[
                NavItem(
                    label='Treasury',
                    url_name='treasurer:dashboard',
                    icon='currency-dollar',
                    order=30,
                    namespace='treasurer',
                ),
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from .models import Meeting

        # Get first meeting for now (multi-meeting support later)
        meeting = Meeting.objects.first()
        if not meeting:
            return []

        from .services import TreasurerService
        service = TreasurerService(meeting)
        summary = service.get_summary()

        return [{
            'template': 'treasurer/widgets/summary.html',
            'context': {
                'summary': summary,
                'meeting': meeting,
            },
            'order': 10,
        }]

    def get_settings_sections(self, request):
        """Return settings sections for global settings page."""
        return [
            SettingsSection(
                name='treasurer',
                title='Treasury',
                template='treasurer/settings_section.html',
                icon='currency-dollar',
                order=30,
                description='Manage treasury settings, categories, and disbursement splits',
            )
        ]

    def get_settings_context(self, request, section_name):
        """Return context for the treasurer settings section."""
        from .models import Meeting, TreasurerSettings, IncomeCategory, ExpenseCategory, DisbursementSplit
        from .forms import TreasurerSettingsForm
        from .services import TreasurerService

        meeting, _ = Meeting.objects.get_or_create(pk=1, defaults={'name': 'Easier Softer Group'})
        service = TreasurerService(meeting)
        settings, _ = service.get_or_create_settings()

        return {
            'form': TreasurerSettingsForm(instance=settings),
            'income_categories': IncomeCategory.objects.filter(meeting=meeting),
            'categories': ExpenseCategory.objects.filter(meeting=meeting),
            'splits': DisbursementSplit.objects.filter(meeting=meeting).prefetch_related('items'),
        }

    def handle_settings_post(self, request, section_name):
        """Handle POST for treasurer settings section."""
        from .models import Meeting
        from .forms import TreasurerSettingsForm
        from .services import TreasurerService

        meeting, _ = Meeting.objects.get_or_create(pk=1, defaults={'name': 'Easier Softer Group'})
        service = TreasurerService(meeting)
        settings, _ = service.get_or_create_settings()

        form = TreasurerSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return 'Treasury settings updated.'
        return None
