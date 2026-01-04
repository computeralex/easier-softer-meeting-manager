"""
Website module registration.
"""
from apps.registry.base_module import BaseModule, ModuleConfig, NavItem, SettingsSection


class WebsiteModule(BaseModule):
    """
    Website module for public-facing content and CMS pages.
    Secretary or GSR can manage.
    """

    @property
    def config(self) -> ModuleConfig:
        return ModuleConfig(
            name='website',
            verbose_name='Website',
            description='Configure public website and CMS pages',
            version='1.0.0',
            url_prefix='website',
            required_positions=['secretary', 'group_rep'],
            read_positions=[],
            icon='globe',
            order=100,  # Last in sidebar nav
            settings_url=None,
            nav_items=[
                NavItem(
                    label='Website',
                    url_name='website_admin:admin',
                    icon='globe',
                    order=100,
                    namespace='website_admin',
                ),
            ]
        )

    def get_dashboard_widgets(self, request):
        """Return widgets for the main dashboard."""
        from .models import WebsitePage
        from apps.treasurer.models import Meeting

        meeting = Meeting.objects.first()
        if not meeting:
            return []

        page_count = WebsitePage.objects.filter(meeting=meeting).count()
        published_count = WebsitePage.objects.filter(
            meeting=meeting,
            is_published=True
        ).count()

        return [{
            'template': 'website/widgets/summary.html',
            'context': {
                'page_count': page_count,
                'published_count': published_count,
            },
            'order': 100,
        }]

    def get_settings_sections(self, request):
        """Return settings sections for global settings page."""
        return [
            SettingsSection(
                name='website',
                title='Website',
                template='website/settings_section.html',
                icon='globe',
                order=100,
                description='Configure public website appearance and module visibility',
            )
        ]

    def get_settings_context(self, request, section_name):
        """Return context for the website settings section."""
        from .models import WebsiteModuleConfig, WebsitePage
        from apps.treasurer.models import Meeting

        meeting, _ = Meeting.objects.get_or_create(pk=1, defaults={'name': 'My Meeting'})
        config = WebsiteModuleConfig.get_instance()
        cms_pages = WebsitePage.objects.filter(meeting=meeting, is_published=True)

        return {
            'config': config,
            'meeting': meeting,
            'cms_pages': cms_pages,
        }

    def handle_settings_post(self, request, section_name):
        """Handle POST for settings form."""
        from .models import WebsiteModuleConfig, WebsitePage

        config = WebsiteModuleConfig.get_instance()

        config.home_page_type = request.POST.get('home_page_type', 'format')

        home_page_id = request.POST.get('home_cms_page')
        if home_page_id:
            config.home_cms_page = WebsitePage.objects.filter(pk=home_page_id).first()
        else:
            config.home_cms_page = None

        config.public_format_enabled = request.POST.get('public_format_enabled') == 'on'
        config.public_readings_enabled = request.POST.get('public_readings_enabled') == 'on'
        config.public_phone_list_enabled = request.POST.get('public_phone_list_enabled') == 'on'
        config.public_treasurer_enabled = request.POST.get('public_treasurer_enabled') == 'on'
        config.show_login_link = request.POST.get('show_login_link') == 'on'

        config.save()
        return 'Website settings updated.'
