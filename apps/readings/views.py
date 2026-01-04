"""
Readings views.
"""
from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, FormView
)

from apps.core.mixins import ServicePositionRequiredMixin
from apps.treasurer.models import Meeting
from .models import Reading, ReadingCategory, ReadingsModuleConfig
from .forms import ReadingForm, ReadingCategoryForm, ImportReadingForm


class MeetingMixin:
    """Mixin to get the current meeting."""

    def get_meeting(self):
        meeting, _ = Meeting.objects.get_or_create(
            pk=1,
            defaults={'name': 'My Meeting'}
        )
        return meeting

    def get_config(self):
        meeting = self.get_meeting()
        config, _ = ReadingsModuleConfig.objects.get_or_create(meeting=meeting)
        return config


# ============================================================================
# Reading CRUD
# ============================================================================

class ReadingListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """List all readings."""
    model = Reading
    template_name = 'readings/reading_list.html'
    context_object_name = 'readings'

    def get_queryset(self):
        qs = Reading.objects.filter(
            meeting=self.get_meeting()
        ).select_related('category')

        # Filter by category if specified
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()
        context['meeting'] = meeting
        context['config'] = self.get_config()
        context['categories'] = ReadingCategory.objects.filter(
            meeting=meeting,
            is_active=True
        )
        context['selected_category'] = self.request.GET.get('category', '')
        context['public_url'] = self.request.build_absolute_uri('/readings/')
        return context


class ReadingCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Add a new reading."""
    model = Reading
    form_class = ReadingForm
    template_name = 'readings/reading_form.html'
    success_url = reverse_lazy('readings:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Reading'
        context['meeting'] = self.get_meeting()
        context['readings_config'] = self.get_config()
        return context

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        # Set order to be last
        max_order = Reading.objects.filter(meeting=self.get_meeting()).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        form.instance.order = max_order + 1
        messages.success(self.request, f'Reading "{form.instance.title}" added.')
        return super().form_valid(form)


class ReadingUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit an existing reading."""
    model = Reading
    form_class = ReadingForm
    template_name = 'readings/reading_form.html'
    success_url = reverse_lazy('readings:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def get_queryset(self):
        return Reading.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Reading'
        context['meeting'] = self.get_meeting()
        context['readings_config'] = self.get_config()
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Reading "{form.instance.title}" updated.')
        return super().form_valid(form)


class ReadingDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a reading."""
    model = Reading
    template_name = 'readings/reading_confirm_delete.html'
    success_url = reverse_lazy('readings:list')

    def get_queryset(self):
        return Reading.objects.filter(meeting=self.get_meeting())

    def form_valid(self, form):
        reading_title = self.object.title
        response = super().form_valid(form)
        messages.success(self.request, f'Reading "{reading_title}" deleted.')
        return response


# ============================================================================
# Category CRUD
# ============================================================================

class CategoryListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """List all categories."""
    model = ReadingCategory
    template_name = 'readings/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ReadingCategory.objects.filter(
            meeting=self.get_meeting()
        ).annotate(
            reading_count=models.Count('readings')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meeting'] = self.get_meeting()
        return context


class CategoryCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Add a new category."""
    model = ReadingCategory
    form_class = ReadingCategoryForm
    template_name = 'readings/category_form.html'
    success_url = reverse_lazy('readings:categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Category'
        return context

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        # Set order to be last
        max_order = ReadingCategory.objects.filter(meeting=self.get_meeting()).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        form.instance.order = max_order + 1
        messages.success(self.request, f'Category "{form.instance.name}" added.')
        return super().form_valid(form)


class CategoryUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit a category."""
    model = ReadingCategory
    form_class = ReadingCategoryForm
    template_name = 'readings/category_form.html'
    success_url = reverse_lazy('readings:categories')

    def get_queryset(self):
        return ReadingCategory.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Category'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated.')
        return super().form_valid(form)


class CategoryDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a category."""
    model = ReadingCategory
    template_name = 'readings/category_confirm_delete.html'
    success_url = reverse_lazy('readings:categories')

    def get_queryset(self):
        return ReadingCategory.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Show count of readings that will be affected
        context['reading_count'] = self.object.readings.count()
        return context

    def form_valid(self, form):
        category_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{category_name}" deleted.')
        return response


# ============================================================================
# Import
# ============================================================================

class ImportView(ServicePositionRequiredMixin, MeetingMixin, FormView):
    """Import a reading from text."""
    template_name = 'readings/import.html'
    form_class = ImportReadingForm
    success_url = reverse_lazy('readings:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def form_valid(self, form):
        meeting = self.get_meeting()

        # Convert plain text to simple HTML (preserve line breaks)
        content = form.cleaned_data['content']
        # Convert newlines to <br> or <p> tags
        paragraphs = content.split('\n\n')
        html_content = ''.join(f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip())

        # Create the reading
        reading = Reading.objects.create(
            meeting=meeting,
            title=form.cleaned_data['title'],
            content=html_content,
            category=form.cleaned_data['category'],
        )

        messages.success(self.request, f'Reading "{reading.title}" imported.')
        return super().form_valid(form)


# ============================================================================
# Settings
# ============================================================================

class SettingsView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Readings settings - redirects to Global Settings."""

    def get(self, request):
        """Redirect to Global Settings readings tab."""
        return redirect(f"{reverse('core:settings')}?tab=readings")

    def post(self, request):
        """Handle toggle for public access."""
        config = self.get_config()
        config.public_enabled = not config.public_enabled
        config.save(update_fields=['public_enabled', 'updated_at'])
        status = 'enabled' if config.public_enabled else 'disabled'
        messages.success(request, f'Public readings {status}.')
        return redirect(f"{reverse('core:settings')}?tab=readings")


class RegenerateTokenView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Regenerate share token."""

    def post(self, request):
        config = self.get_config()
        config.regenerate_token()
        messages.success(request, 'Share link regenerated. Previous links will no longer work.')
        return redirect(f"{reverse('core:settings')}?tab=readings")


class FontSettingsView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Update font size settings."""

    def post(self, request):
        config = self.get_config()
        editor_font_size = request.POST.get('editor_font_size', 'medium')
        display_font_size = request.POST.get('display_font_size', 'medium')

        # Validate choices
        valid_sizes = ['small', 'medium', 'large', 'x-large']
        if editor_font_size in valid_sizes:
            config.editor_font_size = editor_font_size
        if display_font_size in valid_sizes:
            config.display_font_size = display_font_size

        config.save(update_fields=['editor_font_size', 'display_font_size', 'updated_at'])
        messages.success(request, 'Font settings saved.')
        return redirect(f"{reverse('core:settings')}?tab=readings")


# ============================================================================
# Public Views
# ============================================================================

class PublicReadingListView(TemplateView):
    """Public reading list view (no auth required)."""
    template_name = 'readings/public_list.html'

    def get(self, request, token):
        config = get_object_or_404(ReadingsModuleConfig, share_token=token, public_enabled=True)
        return super().get(request, token=token)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token')
        config = get_object_or_404(ReadingsModuleConfig, share_token=token, public_enabled=True)

        context['config'] = config
        context['meeting'] = config.meeting

        # Get categories with their readings
        categories = ReadingCategory.objects.filter(
            meeting=config.meeting,
            is_active=True
        ).prefetch_related(
            models.Prefetch(
                'readings',
                queryset=Reading.objects.filter(is_active=True).order_by('order', 'title')
            )
        ).order_by('order', 'name')

        # Get uncategorized readings
        uncategorized = Reading.objects.filter(
            meeting=config.meeting,
            category__isnull=True,
            is_active=True
        ).order_by('order', 'title')

        context['categories'] = categories
        context['uncategorized_readings'] = uncategorized

        # Get meeting name from config
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()
        context['meeting_name'] = meeting_config.meeting_name

        return context


class PublicReadingDetailView(TemplateView):
    """Public reading detail view with Prev/Next navigation."""
    template_name = 'readings/public_detail.html'

    def get(self, request, token, slug):
        config = get_object_or_404(ReadingsModuleConfig, share_token=token, public_enabled=True)
        reading = get_object_or_404(
            Reading,
            meeting=config.meeting,
            slug=slug,
            is_active=True
        )
        return super().get(request, token=token, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token')
        slug = kwargs.get('slug')

        config = get_object_or_404(ReadingsModuleConfig, share_token=token, public_enabled=True)
        reading = get_object_or_404(
            Reading,
            meeting=config.meeting,
            slug=slug,
            is_active=True
        )

        context['config'] = config
        context['meeting'] = config.meeting
        context['reading'] = reading

        # Get meeting name from config
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()
        context['meeting_name'] = meeting_config.meeting_name

        # Build Prev/Next navigation
        # For now, just use simple ordering by category then order/title
        # Later this will be enhanced for meeting format context
        all_readings = list(Reading.objects.filter(
            meeting=config.meeting,
            is_active=True
        ).order_by('category__order', 'category__name', 'order', 'title'))

        try:
            current_idx = all_readings.index(reading)
            context['prev_reading'] = all_readings[current_idx - 1] if current_idx > 0 else None
            context['next_reading'] = all_readings[current_idx + 1] if current_idx < len(all_readings) - 1 else None
            context['position'] = current_idx + 1
            context['total'] = len(all_readings)
        except (ValueError, IndexError):
            context['prev_reading'] = None
            context['next_reading'] = None
            context['position'] = None
            context['total'] = len(all_readings)

        return context


# ============================================================================
# Reorder Views
# ============================================================================

class ReorderView(ServicePositionRequiredMixin, MeetingMixin, TemplateView):
    """Drag-and-drop reorder page for categories and readings."""
    template_name = 'readings/reorder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.get_meeting()

        # Get categories with their readings
        categories = ReadingCategory.objects.filter(
            meeting=meeting
        ).prefetch_related(
            models.Prefetch(
                'readings',
                queryset=Reading.objects.order_by('order', 'title')
            )
        ).order_by('order', 'name')

        # Get uncategorized readings
        uncategorized = Reading.objects.filter(
            meeting=meeting,
            category__isnull=True
        ).order_by('order', 'title')

        context['categories'] = categories
        context['uncategorized_readings'] = uncategorized
        return context


class ReorderCategoriesView(ServicePositionRequiredMixin, MeetingMixin, View):
    """API endpoint to reorder categories."""

    def post(self, request):
        import json
        from django.http import JsonResponse
        try:
            data = json.loads(request.body)
            order_list = data.get('order', [])

            for idx, cat_id in enumerate(order_list):
                ReadingCategory.objects.filter(
                    pk=cat_id,
                    meeting=self.get_meeting()
                ).update(order=idx)

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class ReorderReadingsView(ServicePositionRequiredMixin, MeetingMixin, View):
    """API endpoint to reorder readings within a category."""

    def post(self, request):
        import json
        from django.http import JsonResponse
        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')  # None for uncategorized
            order_list = data.get('order', [])

            meeting = self.get_meeting()

            for idx, reading_id in enumerate(order_list):
                Reading.objects.filter(
                    pk=reading_id,
                    meeting=meeting
                ).update(order=idx)

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
