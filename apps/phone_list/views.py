"""
Phone List views.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, FormView
)

from apps.core.mixins import ServicePositionRequiredMixin
from apps.treasurer.models import Meeting
from .models import Contact, PhoneListConfig, TimeZone
from .forms import ContactForm, TimeZoneForm, CSVUploadForm, CSVMappingForm, CSVConfirmForm
from .services import PhoneListService


class MeetingMixin:
    """Mixin to get the current meeting."""

    def get_meeting(self):
        meeting, _ = Meeting.objects.get_or_create(
            pk=1,
            defaults={'name': 'My Meeting'}
        )
        return meeting

    def get_service(self):
        return PhoneListService(self.get_meeting())


# ============================================================================
# Contact CRUD
# ============================================================================

class ContactListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """List all contacts."""
    model = Contact
    template_name = 'phone_list/contact_list.html'
    context_object_name = 'contacts'

    def get_queryset(self):
        return Contact.objects.filter(
            meeting=self.get_meeting()
        ).select_related('time_zone')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meeting'] = self.get_meeting()
        # Include config and public URL for sharing
        service = self.get_service()
        config = service.get_or_create_config()
        context['config'] = config
        context['public_url'] = self.request.build_absolute_uri(f'/p/{config.share_token}/')
        return context


class ContactCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Add a new contact."""
    model = Contact
    form_class = ContactForm
    template_name = 'phone_list/contact_form.html'
    success_url = reverse_lazy('phone_list:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Contact'
        context['meeting'] = self.get_meeting()
        return context

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        # Set display order to be last
        max_order = Contact.objects.filter(meeting=self.get_meeting()).aggregate(
            max_order=models.Max('display_order')
        )['max_order'] or 0
        form.instance.display_order = max_order + 1
        messages.success(self.request, f'Contact "{form.instance.name}" added.')
        return super().form_valid(form)


class ContactUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit an existing contact."""
    model = Contact
    form_class = ContactForm
    template_name = 'phone_list/contact_form.html'
    success_url = reverse_lazy('phone_list:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def get_queryset(self):
        return Contact.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Contact'
        context['meeting'] = self.get_meeting()
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Contact "{form.instance.name}" updated.')
        return super().form_valid(form)


class ContactDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a contact."""
    model = Contact
    template_name = 'phone_list/contact_confirm_delete.html'
    success_url = reverse_lazy('phone_list:list')

    def get_queryset(self):
        return Contact.objects.filter(meeting=self.get_meeting())

    def form_valid(self, form):
        contact_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f'Contact "{contact_name}" deleted.')
        return response


class ContactToggleView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Toggle contact visibility (HTMX)."""

    def post(self, request, pk):
        contact = get_object_or_404(
            Contact,
            pk=pk,
            meeting=self.get_meeting()
        )
        contact.is_active = not contact.is_active
        contact.save(update_fields=['is_active', 'updated_at'])

        # Return updated row for HTMX
        if request.htmx:
            from django.template.loader import render_to_string
            html = render_to_string(
                'phone_list/partials/contact_row.html',
                {'contact': contact},
                request=request
            )
            return HttpResponse(html)

        messages.success(
            request,
            f'Contact "{contact.name}" is now {"visible" if contact.is_active else "hidden"}.'
        )
        return redirect('phone_list:list')


# ============================================================================
# Settings
# ============================================================================

class SettingsView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Phone list settings - redirects to Global Settings, handles toggle POST."""

    def get(self, request):
        """Redirect to Global Settings phone_list tab."""
        return redirect(f"{reverse('core:settings')}?tab=phone_list")

    def post(self, request):
        """Handle toggle for public access."""
        service = self.get_service()
        config = service.get_or_create_config()
        config.is_active = not config.is_active
        config.save(update_fields=['is_active', 'updated_at'])
        status = 'enabled' if config.is_active else 'disabled'
        messages.success(request, f'Public phone list {status}.')
        return redirect(f"{reverse('core:settings')}?tab=phone_list")


class RegenerateTokenView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Regenerate share token."""

    def post(self, request):
        service = self.get_service()
        service.regenerate_token()
        messages.success(request, 'Share link regenerated. Previous links will no longer work.')
        return redirect(f"{reverse('core:settings')}?tab=phone_list")


class AddTimeZoneView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Add a new time zone."""

    def post(self, request):
        form = TimeZoneForm(request.POST)
        if form.is_valid():
            tz = form.save(commit=False)
            tz.meeting = self.get_meeting()
            # Set order to be last
            max_order = TimeZone.objects.filter(
                models.Q(meeting=self.get_meeting()) | models.Q(meeting__isnull=True)
            ).aggregate(max_order=models.Max('order'))['max_order'] or 0
            tz.order = max_order + 1
            tz.save()
            messages.success(request, f'Time zone "{tz.display_name}" added.')
        else:
            messages.error(request, 'Please provide both code and display name.')
        return redirect(f"{reverse('core:settings')}?tab=phone_list")


class DeleteTimeZoneView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Delete a time zone."""

    def post(self, request, pk):
        tz = get_object_or_404(TimeZone, pk=pk, meeting=self.get_meeting())
        tz_name = tz.display_name
        tz.delete()
        messages.success(request, f'Time zone "{tz_name}" deleted.')
        return redirect(f"{reverse('core:settings')}?tab=phone_list")


class UpdatePDFSettingsView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Update PDF export settings."""

    def post(self, request):
        service = self.get_service()
        config = service.get_or_create_config()

        # Update settings
        config.pdf_layout = request.POST.get('pdf_layout', 'table')
        config.pdf_font_size = int(request.POST.get('pdf_font_size', 9))
        config.pdf_show_phone = 'pdf_show_phone' in request.POST
        config.pdf_show_email = 'pdf_show_email' in request.POST
        config.pdf_show_time_zone = 'pdf_show_time_zone' in request.POST
        config.pdf_show_sobriety = 'pdf_show_sobriety' in request.POST
        config.pdf_footer_text = request.POST.get('pdf_footer_text', '')

        config.save(update_fields=[
            'pdf_layout', 'pdf_font_size', 'pdf_show_phone', 'pdf_show_email',
            'pdf_show_time_zone', 'pdf_show_sobriety', 'pdf_footer_text', 'updated_at'
        ])

        messages.success(request, 'PDF export settings saved.')
        return redirect(f"{reverse('core:settings')}?tab=phone_list")


# ============================================================================
# CSV Import
# ============================================================================

class ImportUploadView(ServicePositionRequiredMixin, MeetingMixin, FormView):
    """Step 1: Upload CSV file."""
    template_name = 'phone_list/import_upload.html'
    form_class = CSVUploadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['step'] = 1
        return context

    def form_valid(self, form):
        file = form.cleaned_data['file']
        service = self.get_service()

        try:
            headers, rows = service.parse_csv(file)
        except Exception as e:
            messages.error(self.request, f'Error parsing CSV: {str(e)}')
            return self.form_invalid(form)

        if not headers:
            messages.error(self.request, 'CSV file has no headers.')
            return self.form_invalid(form)

        if not rows:
            messages.error(self.request, 'CSV file has no data rows.')
            return self.form_invalid(form)

        # Store in session
        self.request.session['csv_headers'] = headers
        self.request.session['csv_rows'] = rows
        self.request.session['csv_mapping'] = service.auto_detect_mapping(headers)

        return redirect('phone_list:import_map')


class ImportMapView(ServicePositionRequiredMixin, MeetingMixin, FormView):
    """Step 2: Map CSV columns to fields."""
    template_name = 'phone_list/import_map.html'
    form_class = CSVMappingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        headers = self.request.session.get('csv_headers', [])
        kwargs['headers'] = headers
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill with auto-detected mapping
        mapping = self.request.session.get('csv_mapping', {})
        headers = self.request.session.get('csv_headers', [])

        # Reverse mapping: field -> header becomes col_header -> field
        for field, header in mapping.items():
            initial[f'col_{header}'] = field

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['step'] = 2
        context['headers'] = self.request.session.get('csv_headers', [])
        context['row_count'] = len(self.request.session.get('csv_rows', []))
        return context

    def form_valid(self, form):
        mapping = form.get_mapping()
        import_mode = form.cleaned_data['import_mode']

        if 'name' not in mapping:
            messages.error(self.request, 'You must map a column to "Name".')
            return self.form_invalid(form)

        # Store mapping in session
        self.request.session['csv_mapping'] = mapping
        self.request.session['csv_import_mode'] = import_mode

        return redirect('phone_list:import_confirm')


class ImportConfirmView(ServicePositionRequiredMixin, MeetingMixin, FormView):
    """Step 3: Preview and confirm import."""
    template_name = 'phone_list/import_confirm.html'
    form_class = CSVConfirmForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['step'] = 3

        rows = self.request.session.get('csv_rows', [])
        mapping = self.request.session.get('csv_mapping', {})
        import_mode = self.request.session.get('csv_import_mode', 'add')
        meeting = self.get_meeting()

        # Determine how many rows to show (10 -> 100 -> 200 -> ...)
        show_count = int(self.request.GET.get('show', 10))
        next_show = 100 if show_count == 10 else show_count + 100

        # Build preview data
        preview_rows = []
        for row in rows[:show_count]:
            preview = {}
            for field, header in mapping.items():
                preview[field] = row.get(header, '')
            preview_rows.append(preview)

        context['show_count'] = show_count
        context['next_show'] = next_show

        context['preview_rows'] = preview_rows
        context['total_rows'] = len(rows)
        context['mapping'] = mapping
        context['import_mode'] = import_mode
        context['import_mode_display'] = {
            'add': 'Add new contacts only',
            'update': 'Update existing contacts (match by name)',
            'replace': 'Replace all contacts',
        }.get(import_mode, import_mode)

        # Detect unknown time zones
        if 'time_zone' in mapping:
            tz_header = mapping['time_zone']
            # Get all unique TZ values from CSV
            csv_timezones = set()
            for row in rows:
                tz_val = row.get(tz_header, '').strip()
                if tz_val:
                    csv_timezones.add(tz_val)

            # Get existing time zones (global and meeting-specific)
            existing_tzs = TimeZone.objects.filter(
                models.Q(meeting=meeting) | models.Q(meeting__isnull=True),
                is_active=True
            )
            existing_codes = {tz.code.upper() for tz in existing_tzs}

            # Find unknown time zones
            unknown_tzs = []
            for tz_val in sorted(csv_timezones):
                if tz_val.upper() not in existing_codes:
                    # Count how many rows have this TZ
                    count = sum(1 for r in rows if r.get(tz_header, '').strip().upper() == tz_val.upper())
                    unknown_tzs.append({'value': tz_val, 'count': count})

            context['unknown_timezones'] = unknown_tzs
            context['existing_timezones'] = existing_tzs
            # Get any previously saved resolutions from session
            context['tz_resolutions'] = self.request.session.get('csv_tz_resolutions', {})

        return context

    def form_valid(self, form):
        service = self.get_service()
        rows = self.request.session.get('csv_rows', [])
        mapping = self.request.session.get('csv_mapping', {})
        import_mode = self.request.session.get('csv_import_mode', 'add')

        # Collect timezone resolutions from POST data
        tz_resolutions = {}
        for key, value in self.request.POST.items():
            if key.startswith('tz_action_'):
                tz_value = key[10:]  # Remove 'tz_action_' prefix
                action = value
                # Get the map/create details
                map_to = self.request.POST.get(f'tz_map_{tz_value}', '')
                create_name = self.request.POST.get(f'tz_create_{tz_value}', '')
                tz_resolutions[tz_value] = {
                    'action': action,
                    'map_to': map_to,
                    'create_name': create_name,
                }

        added, updated, errors, tz_created = service.import_contacts(
            rows, mapping, import_mode, tz_resolutions, self.get_meeting()
        )

        # Clear session data
        for key in ['csv_headers', 'csv_rows', 'csv_mapping', 'csv_import_mode', 'csv_tz_resolutions']:
            self.request.session.pop(key, None)

        # Show results
        msg_parts = []
        if added:
            msg_parts.append(f'{added} contacts added')
        if updated:
            msg_parts.append(f'{updated} contacts updated')
        if tz_created:
            msg_parts.append(f'{tz_created} time zones created')
        if msg_parts:
            messages.success(self.request, ', '.join(msg_parts) + '.')

        if errors:
            messages.warning(self.request, f'{len(errors)} rows had errors.')

        return redirect('phone_list:list')


# ============================================================================
# Public View
# ============================================================================

class PublicPhoneListView(TemplateView):
    """Public phone list view (no auth required)."""
    template_name = 'phone_list/public.html'

    def get(self, request, token):
        config = get_object_or_404(PhoneListConfig, share_token=token, is_active=True)
        return super().get(request, token=token)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token')
        config = get_object_or_404(PhoneListConfig, share_token=token, is_active=True)
        context['config'] = config
        context['meeting'] = config.meeting
        context['contacts'] = Contact.objects.filter(
            meeting=config.meeting,
            is_active=True
        ).select_related('time_zone')
        # Use the global meeting name from settings
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()
        context['meeting_name'] = meeting_config.meeting_name
        context['sobriety_term'] = meeting_config.get_sobriety_term_label()
        return context


# ============================================================================
# Export Views
# ============================================================================

class ExportPDFView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Export phone list as PDF."""

    def get(self, request):
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()

        service = self.get_service()
        pdf_bytes = service.generate_pdf(
            meeting_name=meeting_config.meeting_name,
            sobriety_term=meeting_config.get_sobriety_term_label()
        )

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"phone_list_{meeting_config.meeting_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportCSVView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Export phone list as CSV."""

    def get(self, request):
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()

        service = self.get_service()
        csv_content = service.export_csv(
            sobriety_term=meeting_config.get_sobriety_term_label()
        )

        response = HttpResponse(csv_content, content_type='text/csv')
        filename = f"phone_list_{meeting_config.meeting_name.replace(' ', '_')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PreviewPDFView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Generate PDF with custom settings (for preview before saving)."""

    def get(self, request):
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()

        # Get settings from query params (use current config as defaults)
        service = self.get_service()
        config = service.get_or_create_config()

        # Override config with query params
        layout = request.GET.get('pdf_layout', config.pdf_layout)
        font_size = int(request.GET.get('pdf_font_size', config.pdf_font_size))
        show_phone = request.GET.get('pdf_show_phone', 'true') == 'true'
        show_email = request.GET.get('pdf_show_email', 'true') == 'true'
        show_time_zone = request.GET.get('pdf_show_time_zone', 'true') == 'true'
        show_sobriety = request.GET.get('pdf_show_sobriety', 'false') == 'true'
        footer_text = request.GET.get('pdf_footer_text', config.pdf_footer_text)

        # Temporarily override config values for PDF generation
        config.pdf_layout = layout
        config.pdf_font_size = font_size
        config.pdf_show_phone = show_phone
        config.pdf_show_email = show_email
        config.pdf_show_time_zone = show_time_zone
        config.pdf_show_sobriety = show_sobriety
        config.pdf_footer_text = footer_text

        # Generate PDF (don't save config changes)
        pdf_bytes = service.generate_pdf(
            meeting_name=meeting_config.meeting_name,
            sobriety_term=meeting_config.get_sobriety_term_label()
        )

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"phone_list_{meeting_config.meeting_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
