"""
Business Meeting views.
"""
from datetime import date

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
)

from apps.core.mixins import ServicePositionRequiredMixin
from apps.treasurer.models import Meeting
from .models import BusinessMeetingFormat, BusinessMeeting
from .forms import BusinessMeetingFormatForm, BusinessMeetingForm


class MeetingMixin:
    """Mixin to get the current meeting."""

    def get_meeting(self):
        meeting, _ = Meeting.objects.get_or_create(
            pk=1,
            defaults={'name': 'Easier Softer Group'}
        )
        return meeting


# ============================================================================
# Business Meeting Format
# ============================================================================

class FormatEditView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit the business meeting format template."""
    model = BusinessMeetingFormat
    form_class = BusinessMeetingFormatForm
    template_name = 'business_meeting/format_edit.html'
    success_url = reverse_lazy('business_meeting:format_edit')

    def get_object(self, queryset=None):
        """Get or create the format for this meeting."""
        meeting = self.get_meeting()
        return BusinessMeetingFormat.get_or_create_for_meeting(meeting)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Business Meeting Format'
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Business meeting format updated.')
        return super().form_valid(form)


# ============================================================================
# Business Meeting CRUD
# ============================================================================

class MeetingListView(ServicePositionRequiredMixin, MeetingMixin, ListView):
    """List all business meetings."""
    model = BusinessMeeting
    template_name = 'business_meeting/meeting_list.html'
    context_object_name = 'meetings'

    def get_queryset(self):
        return BusinessMeeting.objects.filter(
            meeting=self.get_meeting()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meeting'] = self.get_meeting()
        return context


class MeetingCreateView(ServicePositionRequiredMixin, MeetingMixin, CreateView):
    """Create a new business meeting."""
    model = BusinessMeeting
    form_class = BusinessMeetingForm
    template_name = 'business_meeting/meeting_form.html'
    success_url = reverse_lazy('business_meeting:meeting_list')

    def get_initial(self):
        """Set initial date to today."""
        initial = super().get_initial()
        initial['date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Business Meeting'
        context['format_obj'] = BusinessMeetingFormat.get_or_create_for_meeting(
            self.get_meeting()
        )
        return context

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Business meeting for {form.instance.date} created.')
        return super().form_valid(form)


class MeetingUpdateView(ServicePositionRequiredMixin, MeetingMixin, UpdateView):
    """Edit a business meeting."""
    model = BusinessMeeting
    form_class = BusinessMeetingForm
    template_name = 'business_meeting/meeting_form.html'
    success_url = reverse_lazy('business_meeting:meeting_list')

    def get_queryset(self):
        return BusinessMeeting.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Business Meeting - {self.object.date}'
        context['format_obj'] = BusinessMeetingFormat.get_or_create_for_meeting(
            self.get_meeting()
        )
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Business meeting for {form.instance.date} updated.')
        return super().form_valid(form)


class MeetingDetailView(ServicePositionRequiredMixin, MeetingMixin, DetailView):
    """View a business meeting (read-only)."""
    model = BusinessMeeting
    template_name = 'business_meeting/meeting_detail.html'
    context_object_name = 'business_meeting'

    def get_queryset(self):
        return BusinessMeeting.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Business Meeting - {self.object.date}'
        return context


class MeetingDeleteView(ServicePositionRequiredMixin, MeetingMixin, DeleteView):
    """Delete a business meeting."""
    model = BusinessMeeting
    template_name = 'business_meeting/meeting_confirm_delete.html'
    success_url = reverse_lazy('business_meeting:meeting_list')
    context_object_name = 'business_meeting'

    def get_queryset(self):
        return BusinessMeeting.objects.filter(meeting=self.get_meeting())

    def form_valid(self, form):
        messages.success(self.request, f'Business meeting for {self.object.date} deleted.')
        return super().form_valid(form)
