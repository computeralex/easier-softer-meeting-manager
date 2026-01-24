"""
Views for service position management.
"""
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView, View
)
from django.http import HttpResponse

from apps.core.mixins import ServicePositionRequiredMixin
from apps.core.models import ServicePosition, PositionAssignment, User

from .forms import (
    ServicePositionForm, ModulePermissionsForm, PositionAssignmentForm, EndTermForm
)


class PositionListView(ServicePositionRequiredMixin, ListView):
    """List all service positions with current holders."""
    model = ServicePosition
    template_name = 'positions/list.html'
    context_object_name = 'positions'

    def get_queryset(self):
        return ServicePosition.objects.filter(
            is_active=True,
            is_membership_position=False  # Hide membership positions like "Group Member"
        ).prefetch_related(
            'assignments'
        ).annotate(
            current_holder_count=Count(
                'assignments',
                filter=Q(assignments__end_date__isnull=True)
            )
        ).order_by('display_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add holders and status for each position
        for position in context['positions']:
            # Use prefetched data - filter in Python, not via new ORM queries
            # This ensures we see freshly created assignments correctly
            all_assignments = list(position.assignments.all())
            current = [a for a in all_assignments if a.end_date is None]
            primary = [a for a in current if a.is_primary]
            secondary = [a for a in current if not a.is_primary]

            position.current_holders = current
            position.primary_holders = primary
            position.secondary_holders = secondary

            # Status flags using the Python-filtered lists
            position.is_available = len(primary) == 0  # No primary holder
            position.is_vacant = len(current) == 0  # No holders at all
            position.has_multiple_primary = (
                len(primary) > 1 and
                position.warn_on_multiple_holders
            )

            # Check for expiring terms
            position.expiring_assignments = [h for h in current if h.is_term_ending_soon]

        # Count stats
        context['total_positions'] = len(context['positions'])
        # Available = no primary holder (even if covered by secondary)
        context['available_count'] = sum(1 for p in context['positions'] if p.is_available)
        # Vacant = no holders at all
        context['vacant_count'] = sum(1 for p in context['positions'] if p.is_vacant)
        context['expiring_count'] = sum(
            len(p.expiring_assignments) for p in context['positions']
        )

        return context


class PositionDetailView(ServicePositionRequiredMixin, DetailView):
    """View position details, current holders, and history."""
    model = ServicePosition
    template_name = 'positions/detail.html'
    context_object_name = 'position'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        position = self.object

        # Current assignments - split by primary/secondary
        context['primary_assignments'] = position.assignments.filter(
            end_date__isnull=True,
            is_primary=True
        ).select_related('user').order_by('-start_date')

        context['secondary_assignments'] = position.assignments.filter(
            end_date__isnull=True,
            is_primary=False
        ).select_related('user').order_by('-start_date')

        # All current (for backwards compat in templates)
        context['current_assignments'] = position.assignments.filter(
            end_date__isnull=True
        ).select_related('user').order_by('-is_primary', '-start_date')

        # History (past assignments) - last 7 years
        seven_years_ago = date.today() - timedelta(days=7*365)
        context['history'] = position.assignments.filter(
            end_date__isnull=False,
            end_date__gte=seven_years_ago
        ).select_related('user').order_by('-end_date')

        # Status
        context['is_available'] = position.is_available()  # No primary holder
        context['is_vacant'] = position.get_holder_count() == 0  # No holders at all
        context['has_multiple_primary'] = (
            position.get_primary_holder_count() > 1 and
            position.warn_on_multiple_holders
        )

        # Module permissions display
        from apps.registry.module_registry import registry
        modules = registry.get_all_modules()
        perms_display = []
        for name, module in modules.items():
            config = module.config
            level = position.module_permissions.get(config.name, 'none')
            if level != 'none':
                perms_display.append({
                    'name': config.verbose_name,
                    'level': level,
                    'icon': config.icon,
                })
        context['module_permissions'] = perms_display

        return context


class PositionCreateView(ServicePositionRequiredMixin, CreateView):
    """Create a new service position."""
    model = ServicePosition
    form_class = ServicePositionForm
    template_name = 'positions/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Position'
        context['submit_text'] = 'Create Position'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Position "{form.instance.display_name}" created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('positions:detail', kwargs={'pk': self.object.pk})


class PositionUpdateView(ServicePositionRequiredMixin, UpdateView):
    """Edit a service position."""
    model = ServicePosition
    form_class = ServicePositionForm
    template_name = 'positions/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.display_name}'
        context['submit_text'] = 'Save Changes'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Position updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('positions:detail', kwargs={'pk': self.object.pk})


class PositionPermissionsView(ServicePositionRequiredMixin, FormView):
    """Edit module permissions for a position."""
    template_name = 'positions/permissions.html'
    form_class = ModulePermissionsForm

    def get_position(self):
        return get_object_or_404(ServicePosition, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['position'] = self.get_position()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['position'] = self.get_position()
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Module permissions updated.')
        return redirect('positions:detail', pk=self.kwargs['pk'])


class PositionDeleteView(ServicePositionRequiredMixin, DeleteView):
    """Delete a service position (only if no history)."""
    model = ServicePosition
    template_name = 'positions/confirm_delete.html'
    success_url = reverse_lazy('positions:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_history'] = self.object.assignments.exists()
        return context

    def form_valid(self, form):
        if self.object.assignments.exists():
            messages.error(
                self.request,
                'Cannot delete position with assignment history. Deactivate it instead.'
            )
            return redirect('positions:detail', pk=self.object.pk)

        messages.success(self.request, f'Position "{self.object.display_name}" deleted.')
        return super().form_valid(form)


class AssignmentCreateView(ServicePositionRequiredMixin, CreateView):
    """Assign a user to a position."""
    model = PositionAssignment
    form_class = PositionAssignmentForm
    template_name = 'positions/assign.html'

    def get_position(self):
        return get_object_or_404(ServicePosition, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['position'] = self.get_position()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        position = self.get_position()
        context['position'] = position

        # Warn if position already has holders
        if position.get_holder_count() > 0 and position.warn_on_multiple_holders:
            context['warn_multiple'] = True
            context['current_holders'] = position.get_current_holders()

        return context

    def form_valid(self, form):
        position = self.get_position()
        existing_primary = form.get_existing_primary()

        # Check if user already has a primary position
        if existing_primary:
            # Store form data in session and show conflict resolution
            self.request.session['pending_assignment'] = {
                'user_id': form.cleaned_data['user'].pk,
                'is_primary': form.cleaned_data['is_primary'],
                'start_date': str(form.cleaned_data['start_date']),
                'notes': form.cleaned_data.get('notes', ''),
                'position_id': position.pk,
                'existing_assignment_id': existing_primary.pk,
            }
            return redirect('positions:resolve_conflict', pk=position.pk)

        form.instance.position = position
        messages.success(
            self.request,
            f'{form.instance.user} assigned to {position.display_name}.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('positions:detail', kwargs={'pk': self.kwargs['pk']})


class ResolveConflictView(ServicePositionRequiredMixin, TemplateView):
    """Resolve primary position conflict."""
    template_name = 'positions/resolve_conflict.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get('pending_assignment')

        if not pending:
            return context

        context['position'] = get_object_or_404(ServicePosition, pk=pending['position_id'])
        context['user'] = get_object_or_404(User, pk=pending['user_id'])
        context['existing'] = get_object_or_404(PositionAssignment, pk=pending['existing_assignment_id'])
        return context

    def post(self, request, pk):
        pending = request.session.get('pending_assignment')
        if not pending:
            messages.error(request, 'No pending assignment found.')
            return redirect('positions:assign', pk=pk)

        action = request.POST.get('action')
        position = get_object_or_404(ServicePosition, pk=pending['position_id'])
        user = get_object_or_404(User, pk=pending['user_id'])
        existing = get_object_or_404(PositionAssignment, pk=pending['existing_assignment_id'])

        if action == 'make_secondary':
            # Make existing assignment secondary, create new as primary
            existing.is_primary = False
            existing.save(update_fields=['is_primary', 'updated_at'])
            PositionAssignment.objects.create(
                user=user,
                position=position,
                is_primary=True,
                start_date=pending['start_date'],
                notes=pending.get('notes', ''),
            )
            messages.success(
                request,
                f'{user} is now primary for {position.display_name}. '
                f'{existing.position.display_name} changed to secondary.'
            )

        elif action == 'remove_existing':
            # End existing assignment, create new as primary
            existing.end_date = date.today()
            existing.save(update_fields=['end_date', 'updated_at'])
            PositionAssignment.objects.create(
                user=user,
                position=position,
                is_primary=True,
                start_date=pending['start_date'],
                notes=pending.get('notes', ''),
            )
            messages.success(
                request,
                f'{user} is now primary for {position.display_name}. '
                f'Removed from {existing.position.display_name}.'
            )

        elif action == 'cancel':
            messages.info(request, 'Assignment cancelled.')
            del request.session['pending_assignment']
            return redirect('positions:assign', pk=pk)

        # Clean up session
        if 'pending_assignment' in request.session:
            del request.session['pending_assignment']

        return redirect('positions:detail', pk=pk)


class EndTermView(ServicePositionRequiredMixin, FormView):
    """End a user's term in a position."""
    template_name = 'positions/end_term.html'
    form_class = EndTermForm

    def get_assignment(self):
        return get_object_or_404(
            PositionAssignment,
            pk=self.kwargs['assignment_pk'],
            position_id=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = self.get_assignment()
        context['position'] = context['assignment'].position
        return context

    def form_valid(self, form):
        assignment = self.get_assignment()
        assignment.end_date = form.cleaned_data['end_date']
        if form.cleaned_data['notes']:
            assignment.notes = (
                f"{assignment.notes}\n{form.cleaned_data['notes']}".strip()
            )
        assignment.save()

        messages.success(
            self.request,
            f"Term ended for {assignment.user} as {assignment.position.display_name}."
        )
        return redirect('positions:detail', pk=self.kwargs['pk'])


class ReactivateAssignmentView(ServicePositionRequiredMixin, View):
    """Reactivate a historical assignment (clear end_date)."""

    def post(self, request, pk, assignment_pk):
        assignment = get_object_or_404(
            PositionAssignment,
            pk=assignment_pk,
            position_id=pk,
            end_date__isnull=False  # Only historical assignments
        )
        assignment.end_date = None
        assignment.save(update_fields=['end_date', 'updated_at'])

        messages.success(
            request,
            f"Reactivated {assignment.user} as {assignment.position.display_name}."
        )
        return redirect('positions:detail', pk=pk)


class TogglePrimaryView(ServicePositionRequiredMixin, View):
    """Toggle assignment primary status (HTMX)."""

    def post(self, request, assignment_pk):
        assignment = get_object_or_404(
            PositionAssignment,
            pk=assignment_pk,
            end_date__isnull=True  # Only current assignments
        )
        user = assignment.user
        position_name = assignment.position.display_name

        if assignment.is_primary:
            # Unstar - make secondary
            assignment.is_primary = False
            assignment.save(update_fields=['is_primary', 'updated_at'])
            message = f'{position_name} is no longer your primary position'
        else:
            # Star - make primary, unstar any other primary for this user
            PositionAssignment.objects.filter(
                user=user,
                is_primary=True,
                end_date__isnull=True
            ).update(is_primary=False)
            assignment.is_primary = True
            assignment.save(update_fields=['is_primary', 'updated_at'])
            message = f'{position_name} is now your primary position'

        # Return updated partial for HTMX or redirect
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            # Refresh all assignments for this user to update all stars
            assignments = user.position_assignments.filter(
                end_date__isnull=True
            ).select_related('position').order_by('-is_primary', 'position__display_name')
            html = render_to_string(
                'positions/partials/user_positions_list.html',
                {'assignments': assignments, 'user_obj': user},
                request=request
            )
            response = HttpResponse(html)
            response['HX-Trigger'] = f'{{"showToast": "{message}"}}'
            return response

        messages.success(request, message)
        # Redirect back to referring page
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('core:user_list')


class PublicOfficersView(TemplateView):
    """Public directory of service positions."""
    template_name = 'positions/public_officers.html'

    def get_context_data(self, **kwargs):
        from apps.core.models import MeetingConfig

        context = super().get_context_data(**kwargs)
        config = MeetingConfig.get_instance()

        # Check if public display is enabled
        if config.public_officers_display == 'hidden':
            context['hidden'] = True
            context['positions'] = []
            return context

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
        context['meeting_name'] = config.meeting_name

        return context
