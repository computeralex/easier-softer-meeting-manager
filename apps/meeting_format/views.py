"""
Meeting Format views.
"""
from datetime import date

from django.contrib import messages
from django.db import models
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, TemplateView
)

from apps.core.mixins import ServicePositionRequiredMixin
from apps.treasurer.models import Meeting

from .models import (
    FormatBlock, BlockVariation, VariationSchedule, FormatModuleConfig, MeetingType
)
from .forms import (
    FormatBlockForm, BlockVariationForm, VariationScheduleForm,
    FormatModuleConfigForm, MeetingTypeForm
)
from .services import FormatService, ContentRenderer


class MeetingMixin:
    """Mixin to get the current meeting."""

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

    def get_config(self):
        config, _ = FormatModuleConfig.objects.get_or_create(meeting=self.meeting)
        return config


# =============================================================================
# Block Views
# =============================================================================

class BlockListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """Main editor view showing all blocks."""
    model = FormatBlock
    template_name = 'meeting_format/block_list.html'
    context_object_name = 'blocks'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return FormatBlock.objects.filter(
            meeting=self.meeting
        ).prefetch_related(
            'variations',
            'variations__meeting_type',
            'variations__schedules'
        ).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config, _ = FormatModuleConfig.objects.get_or_create(
            meeting=self.meeting
        )
        context['config'] = config
        context['meeting_types'] = MeetingType.objects.filter(
            meeting=self.meeting,
            is_active=True
        )
        return context


class BlockCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Create a new block."""
    model = FormatBlock
    form_class = FormatBlockForm
    template_name = 'meeting_format/block_form.html'
    required_positions = ['secretary', 'group_rep']

    def form_valid(self, form):
        form.instance.meeting = self.meeting
        # Set order to be last
        max_order = FormatBlock.objects.filter(
            meeting=self.meeting
        ).aggregate(max_order=models.Max('order'))['max_order'] or 0
        form.instance.order = max_order + 1
        messages.success(self.request, f'Block "{form.instance.title}" created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


class BlockUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit an existing block."""
    model = FormatBlock
    form_class = FormatBlockForm
    template_name = 'meeting_format/block_form.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return FormatBlock.objects.filter(meeting=self.meeting)

    def form_valid(self, form):
        messages.success(self.request, f'Block "{form.instance.title}" updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


class BlockDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a block."""
    model = FormatBlock
    template_name = 'meeting_format/block_confirm_delete.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return FormatBlock.objects.filter(meeting=self.meeting)

    def form_valid(self, form):
        messages.success(self.request, f'Block "{self.object.title}" deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


class BlockReorderView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Reorder blocks via AJAX or form POST."""
    required_positions = ['secretary', 'group_rep']

    def post(self, request, *args, **kwargs):
        block_id = request.POST.get('block_id')
        direction = request.POST.get('direction')

        if not block_id or direction not in ('up', 'down'):
            messages.error(request, 'Invalid reorder request.')
            return redirect('meeting_format:block_list')

        try:
            block = FormatBlock.objects.get(
                pk=block_id,
                meeting=self.meeting
            )
        except FormatBlock.DoesNotExist:
            messages.error(request, 'Block not found.')
            return redirect('meeting_format:block_list')

        blocks = list(FormatBlock.objects.filter(
            meeting=self.meeting
        ).order_by('order'))

        current_index = None
        for i, b in enumerate(blocks):
            if b.pk == block.pk:
                current_index = i
                break

        if current_index is None:
            return redirect('meeting_format:block_list')

        if direction == 'up' and current_index > 0:
            # Swap with previous
            blocks[current_index], blocks[current_index - 1] = \
                blocks[current_index - 1], blocks[current_index]
        elif direction == 'down' and current_index < len(blocks) - 1:
            # Swap with next
            blocks[current_index], blocks[current_index + 1] = \
                blocks[current_index + 1], blocks[current_index]

        # Update order values
        for i, b in enumerate(blocks):
            if b.order != i:
                b.order = i
                b.save(update_fields=['order'])

        return redirect('meeting_format:block_list')


# =============================================================================
# Variation Views
# =============================================================================

class VariationCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Create a variation for a block."""
    model = BlockVariation
    form_class = BlockVariationForm
    template_name = 'meeting_format/variation_form.html'
    required_positions = ['secretary', 'group_rep']

    def get_block(self):
        return get_object_or_404(
            FormatBlock,
            pk=self.kwargs['block_pk'],
            meeting=self.meeting
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.meeting
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['block'] = self.get_block()
        context['available_slugs'] = ContentRenderer.get_available_slugs(
            self.meeting
        )
        context['format_config'] = self.get_config()
        context['meeting_types'] = MeetingType.objects.filter(
            meeting=self.meeting,
            is_active=True
        )
        return context

    def form_valid(self, form):
        block = self.get_block()
        form.instance.block = block
        # Set order to be last
        max_order = BlockVariation.objects.filter(
            block=block
        ).aggregate(max_order=models.Max('order'))['max_order'] or 0
        form.instance.order = max_order + 1
        # If this is first variation, make it default
        if not block.variations.exists():
            form.instance.is_default = True
        messages.success(self.request, f'Variation "{form.instance.name}" created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


class VariationUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit an existing variation."""
    model = BlockVariation
    form_class = BlockVariationForm
    template_name = 'meeting_format/variation_form.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return BlockVariation.objects.filter(
            block__meeting=self.meeting
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.meeting
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['block'] = self.object.block
        context['available_slugs'] = ContentRenderer.get_available_slugs(
            self.meeting
        )
        context['format_config'] = self.get_config()
        context['meeting_types'] = MeetingType.objects.filter(
            meeting=self.meeting,
            is_active=True
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Variation "{form.instance.name}" updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


class VariationDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a variation."""
    model = BlockVariation
    template_name = 'meeting_format/variation_confirm_delete.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return BlockVariation.objects.filter(
            block__meeting=self.meeting
        )

    def form_valid(self, form):
        messages.success(self.request, f'Variation "{self.object.name}" deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


# =============================================================================
# Schedule Views
# =============================================================================

class ScheduleCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Add a schedule rule to a variation."""
    model = VariationSchedule
    form_class = VariationScheduleForm
    template_name = 'meeting_format/schedule_form.html'
    required_positions = ['secretary', 'group_rep']

    def get_variation(self):
        return get_object_or_404(
            BlockVariation,
            pk=self.kwargs['variation_pk'],
            block__meeting=self.meeting
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variation'] = self.get_variation()
        return context

    def form_valid(self, form):
        form.instance.variation = self.get_variation()
        messages.success(self.request, 'Schedule added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


class ScheduleDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a schedule rule."""
    model = VariationSchedule
    template_name = 'meeting_format/schedule_confirm_delete.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return VariationSchedule.objects.filter(
            variation__block__meeting=self.meeting
        )

    def form_valid(self, form):
        messages.success(self.request, 'Schedule deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:block_list')


# =============================================================================
# Meeting Type Views
# =============================================================================

class MeetingTypeListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """List all meeting types."""
    model = MeetingType
    template_name = 'meeting_format/meeting_type_list.html'
    context_object_name = 'meeting_types'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return MeetingType.objects.filter(
            meeting=self.meeting
        ).annotate(
            variation_count=models.Count('variations')
        )


class MeetingTypeCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Create a new meeting type."""
    model = MeetingType
    form_class = MeetingTypeForm
    template_name = 'meeting_format/meeting_type_form.html'
    required_positions = ['secretary', 'group_rep']

    def form_valid(self, form):
        form.instance.meeting = self.meeting
        # Set order to be last
        max_order = MeetingType.objects.filter(
            meeting=self.meeting
        ).aggregate(max_order=models.Max('order'))['max_order'] or 0
        form.instance.order = max_order + 1
        messages.success(self.request, f'Meeting type "{form.instance.name}" created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:meeting_type_list')


class MeetingTypeUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit an existing meeting type."""
    model = MeetingType
    form_class = MeetingTypeForm
    template_name = 'meeting_format/meeting_type_form.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return MeetingType.objects.filter(meeting=self.meeting)

    def form_valid(self, form):
        messages.success(self.request, f'Meeting type "{form.instance.name}" updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:meeting_type_list')


class MeetingTypeDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a meeting type."""
    model = MeetingType
    template_name = 'meeting_format/meeting_type_confirm_delete.html'
    required_positions = ['secretary', 'group_rep']

    def get_queryset(self):
        return MeetingType.objects.filter(meeting=self.meeting)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variation_count'] = self.object.variations.count()
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Meeting type "{self.object.name}" deleted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('meeting_format:meeting_type_list')


class SelectMeetingTypeView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Select the meeting type for tonight's meeting."""
    required_positions = ['secretary', 'group_rep']

    def post(self, request):
        config = self.get_config()
        meeting_type_id = request.POST.get('meeting_type')

        if meeting_type_id:
            try:
                meeting_type = MeetingType.objects.get(
                    pk=meeting_type_id,
                    meeting=self.meeting,
                    is_active=True
                )
                config.selected_meeting_type = meeting_type
                config.save(update_fields=['selected_meeting_type', 'updated_at'])
                messages.success(request, f'Meeting type set to "{meeting_type.name}".')
            except MeetingType.DoesNotExist:
                messages.error(request, 'Invalid meeting type.')
        else:
            # Clear selection (use default)
            config.selected_meeting_type = None
            config.save(update_fields=['selected_meeting_type', 'updated_at'])
            messages.success(request, 'Meeting type cleared (using default content).')

        return redirect('meeting_format:block_list')


# =============================================================================
# Settings View
# =============================================================================

class FormatSettingsView(ServicePositionRequiredMixin, MeetingMixin, View):
    """Settings view for the format module."""
    required_positions = ['secretary', 'group_rep']

    def post(self, request):
        config = self.get_config()

        # Handle public_enabled toggle
        config.public_enabled = 'public_enabled' in request.POST

        # Handle font sizes
        valid_sizes = ['small', 'medium', 'large', 'x-large']
        editor_font_size = request.POST.get('editor_font_size', 'medium')
        display_font_size = request.POST.get('display_font_size', 'medium')

        if editor_font_size in valid_sizes:
            config.editor_font_size = editor_font_size
        if display_font_size in valid_sizes:
            config.display_font_size = display_font_size

        config.save()
        messages.success(request, 'Format settings updated.')
        return redirect(reverse('core:settings') + '?tab=meeting_format')


# =============================================================================
# Public Views
# =============================================================================

class PublicFormatView(TemplateView):
    """Public view of the meeting format."""
    template_name = 'meeting_format/public.html'

    def get(self, request, *args, **kwargs):
        token = kwargs.get('token')
        try:
            self.config = FormatModuleConfig.objects.select_related(
                'meeting',
                'selected_meeting_type'
            ).get(share_token=token)
        except FormatModuleConfig.DoesNotExist:
            raise Http404("Format not found")

        if not self.config.public_enabled:
            raise Http404("Format not available")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = self.config.meeting

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

        # Get blocks and determine active variations based on selected meeting type
        # Logic: Show all "always shown" (no meeting_type) + matching type-specific
        blocks = FormatBlock.objects.filter(
            meeting=meeting,
            is_active=True
        ).prefetch_related(
            'variations',
            'variations__meeting_type'
        ).order_by('order')

        # Official type is what secretary set on the back-end
        official_type = self.config.selected_meeting_type

        # Preview type can be overridden via ?type= query param
        preview_type_id = self.request.GET.get('type')
        if preview_type_id:
            preview_type = MeetingType.objects.filter(
                pk=preview_type_id,
                meeting=meeting,
                is_active=True
            ).first()
        else:
            preview_type = official_type

        # Get all meeting types for the dropdown
        meeting_types = MeetingType.objects.filter(
            meeting=meeting,
            is_active=True
        ).order_by('order', 'name')

        format_data = []

        for block in blocks:
            # Get variations to display (additive model):
            # 1. All variations with no meeting_type (always shown)
            # 2. Plus variations matching the preview type
            active_variations = []
            for var in block.variations.filter(is_active=True):
                if var.meeting_type is None:
                    # Always shown (base content)
                    active_variations.append(var)
                elif preview_type and var.meeting_type_id == preview_type.pk:
                    # Type-specific, and this type is being previewed
                    active_variations.append(var)

            # Render all active variations
            rendered_contents = []
            for var in active_variations:
                rendered_contents.append({
                    'variation': var,
                    'content': renderer.render(var.content),
                })

            format_data.append({
                'block': block,
                'active_variations': active_variations,
                'rendered_contents': rendered_contents,
                'all_variations': list(block.variations.filter(is_active=True)),
            })

        # Get meeting name from MeetingConfig (General Settings)
        from apps.core.models import MeetingConfig
        meeting_config = MeetingConfig.get_instance()

        context['config'] = self.config
        context['meeting'] = meeting
        context['meeting_name'] = meeting_config.meeting_name
        context['format_data'] = format_data
        context['today'] = date.today()
        context['official_type'] = official_type
        context['preview_type'] = preview_type
        context['meeting_types'] = meeting_types
        return context


class PublicPrintView(PublicFormatView):
    """Print-friendly version of the format."""
    template_name = 'meeting_format/public_print.html'
