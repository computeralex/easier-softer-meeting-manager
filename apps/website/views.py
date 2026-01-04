"""
Website views for public-facing pages and CMS admin.
"""
import json
import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
)
from django.utils.safestring import mark_safe

from apps.core.mixins import ServicePositionRequiredMixin
from apps.core.models import MeetingConfig
from apps.core.validators import validate_image_file
from apps.treasurer.models import Meeting

from .forms import WebsitePageForm
from .models import WebsiteModuleConfig, WebsitePage


# =============================================================================
# MIXINS
# =============================================================================

class PublicMixin:
    """Mixin for public views - no auth required."""

    def get_website_config(self):
        """Get the website configuration singleton."""
        if not hasattr(self, '_website_config'):
            self._website_config = WebsiteModuleConfig.get_instance()
        return self._website_config

    def get_meeting(self):
        """Get the meeting object."""
        return self.get_website_config().meeting

    def get_public_navigation(self):
        """Build navigation for public site."""
        config = self.get_website_config()
        nav = []

        # Home always first
        nav.append({
            'label': 'Home',
            'url': reverse('website:home'),
            'active': self.request.path == '/',
        })

        # Format (if enabled)
        if config.public_format_enabled:
            nav.append({
                'label': 'Meeting Format',
                'url': reverse('website:format'),
                'active': self.request.path.startswith('/format'),
            })

        # Readings (if enabled)
        if config.public_readings_enabled:
            nav.append({
                'label': 'Readings',
                'url': reverse('website:readings'),
                'active': self.request.path.startswith('/readings'),
            })

        # Phone List (if enabled)
        if config.public_phone_list_enabled:
            nav.append({
                'label': 'Phone List',
                'url': reverse('website:phone_list'),
                'active': self.request.path.startswith('/phone-list'),
            })

        # Treasurer Reports (if enabled)
        if config.public_treasurer_enabled:
            nav.append({
                'label': 'Treasurer Reports',
                'url': reverse('website:treasurer'),
                'active': self.request.path.startswith('/treasurer'),
            })

        # Service Positions (if not hidden)
        meeting_config = MeetingConfig.get_instance()
        if meeting_config.public_officers_display != 'hidden':
            nav.append({
                'label': 'Service',
                'url': reverse('website:service'),
                'active': self.request.path.startswith('/service'),
            })

        # CMS pages (published and shown in nav, excluding home page)
        pages = WebsitePage.objects.filter(
            meeting=config.meeting,
            is_published=True,
            show_in_nav=True
        )
        # Exclude the home CMS page if one is set
        if config.home_page_type == 'page' and config.home_cms_page:
            pages = pages.exclude(pk=config.home_cms_page.pk)

        for page in pages:
            nav.append({
                'label': page.title,
                'url': page.get_absolute_url(),
                'active': self.request.path == page.get_absolute_url(),
            })

        return nav

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self.get_website_config()
        context['website_config'] = config
        context['public_nav'] = self.get_public_navigation()
        context['show_login'] = config.show_login_link
        context['meeting_name'] = MeetingConfig.get_instance().meeting_name
        return context


class MeetingMixin:
    """Mixin for admin views that need meeting context."""

    def get_meeting(self):
        meeting, _ = Meeting.objects.get_or_create(
            pk=1,
            defaults={'name': 'My Meeting'}
        )
        return meeting

    @property
    def meeting(self):
        if not hasattr(self, '_meeting'):
            self._meeting = self.get_meeting()
        return self._meeting


# =============================================================================
# PUBLIC VIEWS
# =============================================================================

class HomeView(PublicMixin, TemplateView):
    """Public home page - shows format or CMS page based on config."""

    def get_template_names(self):
        config = self.get_website_config()
        if config.home_page_type == 'page' and config.home_cms_page:
            return ['website/page.html']
        return ['website/home_format.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self.get_website_config()

        if config.home_page_type == 'page' and config.home_cms_page:
            context['page'] = config.home_cms_page
        else:
            # Check for ?type= query param to preview a different meeting type
            from apps.meeting_format.models import MeetingType
            preview_type = None
            preview_type_id = self.request.GET.get('type')
            if preview_type_id:
                meeting = self.get_meeting()
                preview_type = MeetingType.objects.filter(
                    pk=preview_type_id,
                    meeting=meeting,
                    is_active=True
                ).first()

            # Include format data
            format_data, official_type, active_type, meeting_types = self._get_format_data(preview_type)
            context['format_data'] = format_data
            context['official_type'] = official_type
            context['preview_type'] = active_type
            context['meeting_types'] = meeting_types

        return context

    def _get_format_data(self, preview_type=None):
        """Get meeting format blocks and variations using additive model.

        Args:
            preview_type: Optional MeetingType to preview (overrides official selection)

        Returns tuple of (format_data, official_type, preview_type, meeting_types)
        """
        from apps.meeting_format.models import FormatBlock, FormatModuleConfig, MeetingType
        from apps.meeting_format.services import ContentRenderer

        meeting = self.get_meeting()

        # Get format config
        try:
            format_config = FormatModuleConfig.objects.select_related(
                'selected_meeting_type'
            ).get(meeting=meeting)
        except FormatModuleConfig.DoesNotExist:
            return [], None, None, []

        # Get readings token for linking
        readings_token = None
        try:
            from apps.readings.models import ReadingsModuleConfig
            readings_config = ReadingsModuleConfig.objects.get(meeting=meeting)
            if readings_config.public_enabled:
                readings_token = readings_config.share_token
        except:
            pass

        renderer = ContentRenderer(meeting, readings_token)

        # Get blocks
        blocks = FormatBlock.objects.filter(
            meeting=meeting,
            is_active=True
        ).prefetch_related(
            'variations',
            'variations__meeting_type'
        ).order_by('order')

        # Official type is what secretary set
        official_type = format_config.selected_meeting_type

        # Use preview_type if provided, otherwise use official
        active_type = preview_type if preview_type else official_type

        # Get all meeting types for dropdown
        meeting_types = MeetingType.objects.filter(
            meeting=meeting,
            is_active=True
        ).order_by('order', 'name')

        format_data = []

        for block in blocks:
            # Additive model: show "always shown" + matching type-specific
            rendered_contents = []
            for var in block.variations.filter(is_active=True):
                if var.meeting_type is None:
                    # Always shown (base content)
                    rendered_contents.append({
                        'content': renderer.render(var.content),
                        'meeting_type': None,
                    })
                elif active_type and var.meeting_type_id == active_type.pk:
                    # Type-specific, matching current selection
                    rendered_contents.append({
                        'content': renderer.render(var.content),
                        'meeting_type': var.meeting_type,
                    })

            if rendered_contents:
                format_data.append({
                    'block': block,
                    'title': block.title,
                    'rendered_contents': rendered_contents,
                })

        return format_data, official_type, active_type, meeting_types


class PublicFormatView(PublicMixin, TemplateView):
    """Public meeting format page."""
    template_name = 'website/format.html'

    def dispatch(self, request, *args, **kwargs):
        config = WebsiteModuleConfig.get_instance()
        if not config.public_format_enabled:
            raise Http404("Meeting format is not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check for ?type= query param to preview a different meeting type
        from apps.meeting_format.models import MeetingType
        preview_type = None
        preview_type_id = self.request.GET.get('type')
        if preview_type_id:
            meeting = self.get_meeting()
            preview_type = MeetingType.objects.filter(
                pk=preview_type_id,
                meeting=meeting,
                is_active=True
            ).first()

        # Reuse the format data logic from HomeView
        home_view = HomeView()
        home_view.request = self.request
        format_data, official_type, active_type, meeting_types = home_view._get_format_data(preview_type)

        context['format_data'] = format_data
        context['official_type'] = official_type
        context['preview_type'] = active_type
        context['meeting_types'] = meeting_types
        return context


class PublicReadingsView(PublicMixin, TemplateView):
    """Public readings list."""
    template_name = 'website/readings.html'

    def dispatch(self, request, *args, **kwargs):
        config = WebsiteModuleConfig.get_instance()
        if not config.public_readings_enabled:
            raise Http404("Readings are not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()

        from apps.readings.models import Reading, ReadingCategory, ReadingsModuleConfig

        # Get readings config
        try:
            readings_config = ReadingsModuleConfig.objects.get(meeting=meeting)
            context['readings_config'] = readings_config
        except ReadingsModuleConfig.DoesNotExist:
            context['readings_config'] = None

        # Get categories with their readings
        categories = ReadingCategory.objects.filter(
            meeting=meeting,
            is_active=True
        ).prefetch_related(
            models.Prefetch(
                'readings',
                queryset=Reading.objects.filter(is_active=True).order_by('order', 'title')
            )
        ).order_by('order', 'name')

        # Get uncategorized readings
        uncategorized = Reading.objects.filter(
            meeting=meeting,
            category__isnull=True,
            is_active=True
        ).order_by('order', 'title')

        context['categories'] = categories
        context['uncategorized_readings'] = uncategorized

        return context


class PublicReadingDetailView(PublicMixin, TemplateView):
    """Public reading detail view."""
    template_name = 'website/reading_detail.html'

    def dispatch(self, request, *args, **kwargs):
        config = WebsiteModuleConfig.get_instance()
        if not config.public_readings_enabled:
            raise Http404("Readings are not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        meeting = self.get_meeting()

        from apps.readings.models import Reading, ReadingsModuleConfig

        reading = get_object_or_404(
            Reading,
            meeting=meeting,
            slug=slug,
            is_active=True
        )
        context['reading'] = reading

        # Get readings config
        try:
            readings_config = ReadingsModuleConfig.objects.get(meeting=meeting)
            context['readings_config'] = readings_config
        except ReadingsModuleConfig.DoesNotExist:
            context['readings_config'] = None

        # Get all readings for prev/next navigation
        all_readings = list(Reading.objects.filter(
            meeting=meeting,
            is_active=True
        ).order_by('category__order', 'category__name', 'order', 'title'))

        # Find current index for prev/next
        try:
            current_index = all_readings.index(reading)
            context['current_index'] = current_index + 1
            context['total_readings'] = len(all_readings)

            if current_index > 0:
                context['prev_reading'] = all_readings[current_index - 1]
            if current_index < len(all_readings) - 1:
                context['next_reading'] = all_readings[current_index + 1]
        except ValueError:
            pass

        return context


class PublicPhoneListView(PublicMixin, TemplateView):
    """Public phone list page."""
    template_name = 'website/phone_list.html'

    def dispatch(self, request, *args, **kwargs):
        config = WebsiteModuleConfig.get_instance()
        if not config.public_phone_list_enabled:
            raise Http404("Phone list is not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()

        from apps.phone_list.models import Contact, PhoneListConfig

        # Get phone list config
        try:
            phone_config = PhoneListConfig.objects.get(meeting=meeting)
            context['phone_config'] = phone_config
        except PhoneListConfig.DoesNotExist:
            context['phone_config'] = None

        # Get active contacts
        contacts = Contact.objects.filter(
            meeting=meeting,
            is_active=True
        ).select_related('time_zone').order_by('first_name', 'last_name')

        context['contacts'] = contacts

        return context


class PublicTreasurerView(PublicMixin, TemplateView):
    """Public treasurer reports list."""
    template_name = 'website/treasurer.html'

    def dispatch(self, request, *args, **kwargs):
        config = WebsiteModuleConfig.get_instance()
        if not config.public_treasurer_enabled:
            raise Http404("Treasurer reports are not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()

        from apps.treasurer.models import TreasurerReport

        # Get active reports (not archived/deleted)
        reports = TreasurerReport.objects.filter(
            meeting=meeting,
            is_archived=False
        ).order_by('-end_date')

        context['reports'] = reports

        return context


class PublicTreasurerDetailView(PublicMixin, TemplateView):
    """Public treasurer report detail."""
    template_name = 'website/treasurer_detail.html'

    def dispatch(self, request, *args, **kwargs):
        config = WebsiteModuleConfig.get_instance()
        if not config.public_treasurer_enabled:
            raise Http404("Treasurer reports are not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()
        report_pk = self.kwargs.get('pk')

        from apps.treasurer.models import TreasurerReport, TreasurerRecord

        # Get the specific active report
        report = get_object_or_404(
            TreasurerReport,
            pk=report_pk,
            meeting=meeting,
            is_archived=False
        )
        context['report'] = report

        # Get transactions for this report period
        transactions = TreasurerRecord.objects.filter(
            meeting=meeting,
            date__gte=report.start_date,
            date__lte=report.end_date
        ).select_related('category', 'income_category').order_by('date')

        context['transactions'] = transactions

        # Separate income and expenses
        context['income_records'] = [t for t in transactions if t.type == 'income']
        context['expense_records'] = [t for t in transactions if t.type == 'expense']

        return context


class PublicServiceView(PublicMixin, TemplateView):
    """Public service positions page."""
    template_name = 'positions/public_officers.html'

    def dispatch(self, request, *args, **kwargs):
        config = MeetingConfig.get_instance()
        if config.public_officers_display == 'hidden':
            raise Http404("Service positions are not publicly available")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = MeetingConfig.get_instance()

        from apps.core.models import ServicePosition

        # Get all active positions (alphabetically)
        positions = ServicePosition.objects.filter(
            is_active=True
        ).order_by('display_name')

        # Add holder info to each position for the template
        for position in positions:
            position.primary_holders_list = list(position.get_primary_holders())
            position.is_filled = len(position.primary_holders_list) > 0

        context['positions'] = positions
        context['show_holder_names'] = config.public_officers_display == 'names'
        context['sobriety_term'] = config.get_sobriety_term_label()
        context['hidden'] = False

        return context


class CMSPageView(PublicMixin, DetailView):
    """Display a CMS page."""
    model = WebsitePage
    template_name = 'website/page.html'
    context_object_name = 'page'

    def get_queryset(self):
        return WebsitePage.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.object

        # Always render fresh from JSON (templates may have changed)
        if page.content:
            from apps.website.puck.renderer import render_puck_content
            context['page_content'] = render_puck_content(page.content)
        else:
            context['page_content'] = ''

        return context


class PublicLoginView(TemplateView):
    """Login page styled for public site."""
    template_name = 'website/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meeting_name'] = MeetingConfig.get_instance().meeting_name
        return context

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', reverse('core:dashboard'))
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
            return self.get(request, *args, **kwargs)


# =============================================================================
# ADMIN VIEWS (authenticated)
# =============================================================================

class WebsiteAdminView(ServicePositionRequiredMixin, MeetingMixin, TemplateView):
    """Website admin dashboard - overview of pages and settings."""
    template_name = 'website/admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = WebsiteModuleConfig.get_instance()
        context['pages'] = WebsitePage.objects.filter(meeting=self.meeting)
        context['published_count'] = context['pages'].filter(is_published=True).count()
        return context


class PageListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """List all CMS pages."""
    model = WebsitePage
    template_name = 'website/page_list.html'
    context_object_name = 'pages'

    def get_queryset(self):
        return WebsitePage.objects.filter(meeting=self.meeting)


class PageCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Create a new CMS page."""
    model = WebsitePage
    form_class = WebsitePageForm
    template_name = 'website/page_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.meeting
        return kwargs

    def form_valid(self, form):
        form.instance.meeting = self.meeting
        messages.success(self.request, 'Page created! Now design your content.')
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to Puck editor after creating
        return reverse('website_admin:puck_editor', kwargs={'pk': self.object.pk})


class PageUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit a CMS page."""
    model = WebsitePage
    form_class = WebsitePageForm
    template_name = 'website/page_form.html'

    def get_queryset(self):
        return WebsitePage.objects.filter(meeting=self.meeting)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.meeting
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Page updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('website_admin:page_list')


class PageDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a CMS page."""
    model = WebsitePage
    template_name = 'website/page_confirm_delete.html'
    success_url = reverse_lazy('website_admin:page_list')

    def get_queryset(self):
        return WebsitePage.objects.filter(meeting=self.meeting)

    def form_valid(self, form):
        messages.success(self.request, 'Page deleted successfully.')
        return super().form_valid(form)


# =============================================================================
# PUCK EDITOR VIEWS
# =============================================================================

class PuckEditorView(ServicePositionRequiredMixin, MeetingMixin, TemplateView):
    """Full-page Puck visual editor for CMS pages."""
    template_name = 'website/puck_editor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_pk = self.kwargs.get('pk')

        if page_pk:
            # Editing existing page
            page = get_object_or_404(WebsitePage, pk=page_pk, meeting=self.meeting)
            initial_data = page.content if page.content else {'content': [], 'root': {}}
            save_url = reverse('website_admin:page_save_content', kwargs={'pk': page_pk})
        else:
            # Creating new page - create a blank page first
            page = WebsitePage.objects.create(
                meeting=self.meeting,
                title='Untitled Page',
                slug=f'untitled-{WebsitePage.objects.filter(meeting=self.meeting).count() + 1}',
                content={'content': [], 'root': {}},
                is_published=False
            )
            initial_data = {'content': [], 'root': {}}
            save_url = reverse('website_admin:page_save_content', kwargs={'pk': page.pk})

        context['page'] = page
        context['initial_data'] = initial_data  # json_script handles encoding
        context['save_url'] = save_url
        context['back_url'] = reverse('website_admin:page_list')

        return context


@method_decorator(csrf_protect, name='dispatch')
class SavePageContentView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Save Puck editor content for a page."""

    def post(self, request, pk):
        page = get_object_or_404(WebsitePage, pk=pk, meeting=self.meeting)

        try:
            data = json.loads(request.body)
            page.content = data
            page.save()  # This will also render the HTML via the model's save method

            return JsonResponse({
                'success': True,
                'redirect': reverse('website_admin:page_list'),
                'message': 'Page saved successfully.'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_protect, name='dispatch')
class UploadImageView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Handle image uploads for the Puck editor."""

    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)

        uploaded_file = request.FILES['file']

        # Validate file type using magic bytes (not just extension)
        try:
            validate_image_file(uploaded_file)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

        # Get validated extension from filename
        ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else 'jpg'

        # Generate unique filename
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'puck_uploads')
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_name)

        # Save file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Return URL
        file_url = f"{settings.MEDIA_URL}puck_uploads/{unique_name}"

        return JsonResponse({
            'success': True,
            'url': file_url
        })
