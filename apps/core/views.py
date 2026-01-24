"""
Core views: dashboard, login, logout, settings, utilities, user management.
"""
import io
import json
import secrets
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import models
from django.contrib import messages
from django.contrib.auth import views as auth_views, update_session_auth_hash
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core import management
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, CreateView, UpdateView, DeleteView, RedirectView

from .mixins import ServicePositionRequiredMixin, SuperuserRequiredMixin
from .models import MeetingConfig, User, ServicePosition, PositionAssignment
from .forms import (
    MeetingConfigForm, UserProfileForm, UserForm, UserInviteForm, PasswordChangeFormStyled,
    SetupWizardForm
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard after login."""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get dashboard widgets from all modules
        from apps.registry.module_registry import registry
        widgets = []
        for module in registry.get_modules_for_user(self.request.user):
            widgets.extend(module.get_dashboard_widgets(self.request))
        context['widgets'] = sorted(widgets, key=lambda w: w.get('order', 100))
        return context


class LoginView(RedirectView):
    """Redirect to the main login page."""
    pattern_name = 'website:login'


class LogoutView(auth_views.LogoutView):
    """Custom logout view."""
    pass


class SetupWizardView(LoginRequiredMixin, TemplateView):
    """Initial setup wizard for new installations."""
    template_name = 'core/setup_wizard.html'

    # Default service positions to offer
    DEFAULT_POSITIONS = [
        {'name': 'secretary', 'display_name': 'Secretary', 'description': 'Facilitates meetings'},
        {'name': 'treasurer', 'display_name': 'Treasurer', 'description': 'Handles group finances'},
        {'name': 'gsr', 'display_name': 'GSR', 'description': 'General Service Representative'},
        {'name': 'literature', 'display_name': 'Literature Person', 'description': 'Manages literature inventory'},
        {'name': 'greeter', 'display_name': 'Greeter', 'description': 'Welcomes newcomers'},
        {'name': 'coffee', 'display_name': 'Coffee Maker', 'description': 'Prepares refreshments'},
    ]

    def get_step(self):
        return self.request.session.get('setup_step', 1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['step'] = self.get_step()
        context['config'] = MeetingConfig.get_instance()
        context['default_positions'] = self.DEFAULT_POSITIONS
        context['existing_positions'] = list(ServicePosition.objects.values_list('name', flat=True))
        return context

    def post(self, request, *args, **kwargs):
        # Handle skip actions (available on any step)
        if 'skip_later' in request.POST:
            request.session['setup_skipped'] = True
            request.session.pop('setup_step', None)
            messages.info(request, "No problem! We'll remind you next time you log in.")
            return redirect('core:dashboard')
        elif 'skip_forever' in request.POST:
            config = MeetingConfig.get_instance()
            config.setup_status = 'dismissed'
            config.save()
            request.session.pop('setup_step', None)
            messages.info(request, "Setup wizard dismissed. You can configure settings anytime from the Settings page.")
            return redirect('core:dashboard')

        step = self.get_step()

        if step == 1:
            # Save group name
            meeting_name = request.POST.get('meeting_name', '').strip()
            if meeting_name:
                config = MeetingConfig.get_instance()
                config.meeting_name = meeting_name
                config.save()
                request.session['setup_step'] = 2
                return redirect('core:setup_wizard')
            else:
                messages.error(request, "Please enter a group name.")
                return redirect('core:setup_wizard')

        elif step == 2:
            # Create selected positions
            selected = request.POST.getlist('positions')
            for pos_data in self.DEFAULT_POSITIONS:
                if pos_data['name'] in selected:
                    ServicePosition.objects.get_or_create(
                        name=pos_data['name'],
                        defaults={
                            'display_name': pos_data['display_name'],
                            'description': pos_data['description'],
                            'is_active': True,
                        }
                    )

            # Complete setup
            config = MeetingConfig.get_instance()
            config.setup_status = 'completed'
            config.save()
            request.session.pop('setup_step', None)
            messages.success(request, f'Welcome to {config.meeting_name}! Your group is ready to use.')
            return redirect('core:dashboard')

        return redirect('core:setup_wizard')


class SettingsView(LoginRequiredMixin, TemplateView):
    """Global application settings with modular sections."""
    template_name = 'core/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.registry.module_registry import registry

        # Get active tab from URL
        active_tab = self.request.GET.get('tab', 'general')
        context['active_tab'] = active_tab

        # General settings form
        context['form'] = MeetingConfigForm(instance=MeetingConfig.get_instance())

        # Get module settings sections
        context['module_sections'] = registry.get_settings_sections_for_user(self.request)

        return context

    def post(self, request, *args, **kwargs):
        from apps.registry.module_registry import registry

        active_tab = request.GET.get('tab', 'general')

        if active_tab == 'general':
            # Handle general settings form
            form = MeetingConfigForm(request.POST, instance=MeetingConfig.get_instance())
            if form.is_valid():
                form.save()
                messages.success(request, 'Settings saved.')
            else:
                messages.error(request, 'Please correct the errors below.')
                return self.render_to_response(self.get_context_data(form=form))
        else:
            # Find the module and section, delegate to module
            for section in registry.get_settings_sections_for_user(request):
                if section['name'] == active_tab:
                    result = section['module'].handle_settings_post(request, active_tab)
                    if result:
                        messages.success(request, result)
                    break

        return redirect(f"{reverse_lazy('core:settings')}?tab={active_tab}")


class ProfileView(LoginRequiredMixin, FormView):
    """User profile editing."""
    template_name = 'core/profile.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('core:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)


class UtilitiesView(ServicePositionRequiredMixin, TemplateView):
    """Utilities page with backup/restore options. Restricted to service positions."""
    template_name = 'core/utilities.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # List existing backups
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backups = []
        if backup_dir.exists():
            for f in sorted(backup_dir.glob('backup_*.json'), reverse=True):
                stat = f.stat()
                backups.append({
                    'filename': f.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                })
        context['backups'] = backups
        return context


class BackupDownloadView(SuperuserRequiredMixin, View):
    """Download a backup file (JSON export of all data). Superuser only - contains password hashes."""

    def get(self, request):
        # Generate backup using dumpdata
        output = io.StringIO()
        management.call_command(
            'dumpdata',
            '--indent', '2',
            '--exclude', 'contenttypes',
            '--exclude', 'auth.permission',
            '--exclude', 'sessions',
            stdout=output
        )

        # Create response with JSON file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'

        response = HttpResponse(output.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class BackupRestoreView(SuperuserRequiredMixin, View):
    """Restore data from uploaded backup file. Superuser only."""

    # Models that are NEVER restored (security + local settings)
    BLOCKED_MODELS = {
        'core.user',            # NEVER restore users - prevents lockout/privilege escalation
        'core.meetingconfig',   # Local settings (name, setup_status) - don't overwrite
        'auth.user',            # Django's default user model (just in case)
        'admin.logentry',       # Admin action history
        'sessions.session',     # Active sessions
        'axes.accessattempt',   # Login throttling
        'axes.accesslog',       # Login logs
        'axes.accessfailurelog', # Failed login logs
    }

    # Models to clear before restore (order matters for foreign keys)
    CLEARABLE_MODELS = [
        'positions.positionassignment',  # Clear assignments first (FK to positions and users)
        'core.positionassignment',
        'finance.transaction',
        'finance.budget',
        'finance.category',
        'literature.inventoryitem',
        'literature.order',
        'core.serviceposition',
        # Don't clear users - too dangerous, could lock yourself out
    ]

    def post(self, request):
        if 'backup_file' not in request.FILES:
            messages.error(request, 'No file uploaded.')
            return redirect('core:utilities')

        backup_file = request.FILES['backup_file']
        replace_data = request.POST.get('replace_data') == 'on'

        # Validate it's JSON
        if not backup_file.name.endswith('.json'):
            messages.error(request, 'Please upload a .json backup file.')
            return redirect('core:utilities')

        try:
            # Read and validate JSON
            content = backup_file.read().decode('utf-8')
            data = json.loads(content)

            # Validate backup structure
            if not isinstance(data, list):
                messages.error(request, 'Invalid backup format: expected a list.')
                return redirect('core:utilities')

            # Filter out blocked models (session/log data we don't want)
            filtered_data = []
            skipped_count = 0
            models_in_backup = set()
            for item in data:
                if not isinstance(item, dict) or 'model' not in item:
                    messages.error(request, 'Invalid backup format: malformed entry.')
                    return redirect('core:utilities')
                model_name = item['model'].lower()
                if model_name in self.BLOCKED_MODELS:
                    skipped_count += 1
                else:
                    filtered_data.append(item)
                    models_in_backup.add(model_name)

            # If replace mode, clear existing data for models in the backup
            if replace_data:
                from django.apps import apps
                for model_path in self.CLEARABLE_MODELS:
                    if model_path in models_in_backup:
                        try:
                            app_label, model_name = model_path.split('.')
                            model = apps.get_model(app_label, model_name)
                            deleted_count = model.objects.all().delete()[0]
                        except LookupError:
                            pass  # Model doesn't exist in this installation

            # Save filtered data to temp file and load
            temp_path = Path(settings.BASE_DIR) / 'backups' / 'temp_restore.json'
            temp_path.parent.mkdir(exist_ok=True)
            temp_path.write_text(json.dumps(filtered_data, indent=2))

            # Run loaddata
            management.call_command('loaddata', str(temp_path))

            # Clean up temp file
            temp_path.unlink()

            messages.success(request, 'Backup restored successfully.')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON file.')
        except Exception as e:
            messages.error(request, f'Error restoring backup: {str(e)}')

        return redirect('core:utilities')


class ServerBackupDownloadView(SuperuserRequiredMixin, View):
    """Download a specific backup file from the server. Superuser only."""

    def get(self, request, filename):
        # Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            messages.error(request, 'Invalid filename.')
            return redirect('core:utilities')

        backup_path = Path(settings.BASE_DIR) / 'backups' / filename

        if not backup_path.exists() or not backup_path.is_file():
            messages.error(request, 'Backup file not found.')
            return redirect('core:utilities')

        # Read and serve the file
        content = backup_path.read_text()
        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ServerBackupDeleteView(SuperuserRequiredMixin, View):
    """Delete a specific backup file from the server. Superuser only."""

    def post(self, request, filename):
        # Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            messages.error(request, 'Invalid filename.')
            return redirect('core:utilities')

        backup_path = Path(settings.BASE_DIR) / 'backups' / filename

        if not backup_path.exists() or not backup_path.is_file():
            messages.error(request, 'Backup file not found.')
            return redirect('core:utilities')

        try:
            backup_path.unlink()
            messages.success(request, f'Backup "{filename}" deleted.')
        except Exception as e:
            messages.error(request, f'Error deleting backup: {str(e)}')

        return redirect('core:utilities')


# =============================================================================
# User Management Views
# =============================================================================

class UserListView(ServicePositionRequiredMixin, ListView):
    """List all users with their positions."""
    model = User
    template_name = 'core/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.prefetch_related('positions').order_by('-is_active', 'email')


def send_password_reset_email(user, request):
    """
    Send a password reset email to a user.
    Returns True if email was sent successfully, False otherwise.
    """
    try:
        # Use Django's PasswordResetForm to send the email
        form = PasswordResetForm(data={'email': user.email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                token_generator=default_token_generator,
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name='core/password_reset_email.html',
                subject_template_name='core/password_reset_subject.txt',
            )
            return True
    except Exception:
        pass
    return False


class UserCreateView(ServicePositionRequiredMixin, CreateView):
    """Create a new user."""
    model = User
    form_class = UserForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('core:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add User'
        return context

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        # Create user with unusable password (they'll set it via reset link)
        user = form.save(commit=False)
        user.set_unusable_password()
        user.save()
        form.save_m2m()  # Save positions

        # Auto-assign membership position (e.g., "Group Member")
        membership_position = ServicePosition.objects.filter(
            is_membership_position=True, is_active=True
        ).first()
        if membership_position:
            PositionAssignment.objects.get_or_create(
                user=user,
                position=membership_position,
                end_date__isnull=True,
                defaults={'is_primary': False}
            )

        # Send password reset email so user can set their own password
        if send_password_reset_email(user, self.request):
            messages.success(
                self.request,
                f'User "{user.email}" created. A password reset email has been sent.'
            )
        else:
            # Email failed - generate temp password as fallback
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            user.save()
            messages.warning(
                self.request,
                f'User "{user.email}" created but email could not be sent. '
                f'Temporary password: {password}'
            )

        return redirect(self.get_success_url())


class UserUpdateView(ServicePositionRequiredMixin, UpdateView):
    """Edit an existing user."""
    model = User
    form_class = UserForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('core:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit User: {self.object.email}'
        # Add current position assignments for star toggle UI
        context['current_assignments'] = self.object.position_assignments.filter(
            end_date__isnull=True
        ).select_related('position').order_by('-is_primary', 'position__display_name')
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'User updated.')
        return redirect(self.success_url)


class UserDeleteView(ServicePositionRequiredMixin, DeleteView):
    """Delete a user."""
    model = User
    template_name = 'core/user_confirm_delete.html'
    success_url = reverse_lazy('core:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete User'
        return context

    def form_valid(self, form):
        user = self.get_object()
        if user == self.request.user:
            messages.error(self.request, 'You cannot delete yourself.')
            return redirect('core:user_list')
        messages.success(self.request, f'User "{user.email}" deleted.')
        return super().form_valid(form)


class UserToggleView(ServicePositionRequiredMixin, View):
    """Toggle user active status (HTMX)."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            messages.error(request, 'You cannot deactivate yourself.')
            return redirect('core:user_list')

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User "{user.email}" {status}.')
        return redirect('core:user_list')


class SendPasswordResetEmailView(ServicePositionRequiredMixin, View):
    """Send a password reset email to a user (admin action)."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if not user.is_active:
            messages.error(request, f'Cannot send reset email to inactive user "{user.email}".')
            return redirect('core:user_list')

        if send_password_reset_email(user, request):
            messages.success(request, f'Password reset email sent to "{user.email}".')
        else:
            messages.error(request, f'Failed to send password reset email to "{user.email}".')

        # Redirect back to referring page or user list
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('core:user_list')


class UserInviteView(ServicePositionRequiredMixin, FormView):
    """Invite a new user by email."""
    form_class = UserInviteForm
    template_name = 'core/user_invite.html'
    success_url = reverse_lazy('core:user_list')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        first_name = form.cleaned_data.get('first_name', '')
        last_name = form.cleaned_data.get('last_name', '')
        primary_position = form.cleaned_data.get('primary_position')
        secondary_positions = form.cleaned_data.get('secondary_positions', [])
        send_email_flag = form.cleaned_data.get('send_email', True)

        # Create user (placeholder if no email)
        if email:
            password = secrets.token_urlsafe(12)
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
        else:
            # Placeholder user - no email, can't log in
            user = User.objects.create_placeholder(
                first_name=first_name,
                last_name=last_name,
            )

        # Create primary position assignment
        if primary_position:
            PositionAssignment.objects.create(
                user=user,
                position=primary_position,
                is_primary=True
            )

        # Create secondary position assignments
        for position in secondary_positions:
            PositionAssignment.objects.create(
                user=user,
                position=position,
                is_primary=False
            )

        # Auto-assign membership position (e.g., "Group Member")
        membership_position = ServicePosition.objects.filter(
            is_membership_position=True, is_active=True
        ).first()
        if membership_position:
            PositionAssignment.objects.get_or_create(
                user=user,
                position=membership_position,
                end_date__isnull=True,
                defaults={'is_primary': False}
            )

        # Handle messaging based on user type
        if not email:
            # Placeholder user created
            display_name = user.get_full_name() or 'Placeholder user'
            messages.success(self.request, f'Placeholder "{display_name}" created.')
        elif send_email_flag:
            # Send welcome email
            login_url = self.request.build_absolute_uri(reverse('website:login'))
            subject = 'Welcome to Meeting Manager'
            message = f"""Hello{' ' + first_name if first_name else ''},

You have been invited to Meeting Manager.

Your login credentials:
Email: {email}
Password: {password}

Login at: {login_url}

Please change your password after logging in.
"""
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(self.request, f'User "{email}" invited. Welcome email sent.')
            except Exception as e:
                messages.warning(
                    self.request,
                    f'User "{email}" created but email failed to send. '
                    f'Temporary password: {password}'
                )
        else:
            # Show password on screen
            messages.success(
                self.request,
                f'User "{email}" created. Temporary password: {password}'
            )

        return redirect(self.success_url)


# =============================================================================
# Password Management Views
# =============================================================================

class PasswordChangeView(LoginRequiredMixin, FormView):
    """Change own password."""
    form_class = PasswordChangeFormStyled
    template_name = 'core/password_change.html'
    success_url = reverse_lazy('core:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        # Keep user logged in after password change
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Password changed successfully.')
        return redirect(self.success_url)


class PasswordResetView(auth_views.PasswordResetView):
    """Request password reset email."""
    template_name = 'core/password_reset.html'
    email_template_name = 'core/password_reset_email.html'
    subject_template_name = 'core/password_reset_subject.txt'
    success_url = reverse_lazy('core:password_reset_done')


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Password reset email sent."""
    template_name = 'core/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Enter new password after clicking email link."""
    template_name = 'core/password_reset_confirm.html'
    success_url = reverse_lazy('core:password_reset_complete')


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Password reset complete."""
    template_name = 'core/password_reset_complete.html'


# =============================================================================
# User Search API (HTMX)
# =============================================================================

class UserSearchView(ServicePositionRequiredMixin, View):
    """HTMX endpoint for searching users by name or email."""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        users = []

        if len(query) >= 2:
            # Split query into words and require all to match somewhere
            words = query.split()
            qs = User.objects.filter(is_active=True)

            for word in words:
                qs = qs.filter(
                    models.Q(first_name__icontains=word) |
                    models.Q(last_name__icontains=word) |
                    models.Q(email__icontains=word)
                )

            users = qs.order_by('first_name', 'last_name')[:10]

        html = ''.join(
            f'<button type="button" class="list-group-item list-group-item-action user-search-result" '
            f'data-user-id="{u.pk}" data-user-name="{u.get_full_name() or u.email or "Unnamed"}">'
            f'<strong>{u.get_full_name() or "Unnamed"}</strong>'
            f'{f" <small class=text-muted>({u.email})</small>" if u.email else " <small class=text-muted>(no email)</small>"}'
            f'</button>'
            for u in users
        )

        if not html and query:
            html = '<div class="list-group-item text-muted">No users found</div>'

        return HttpResponse(html)


class QuickCreateUserView(ServicePositionRequiredMixin, View):
    """HTMX endpoint for quickly creating a placeholder user."""

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not first_name:
            return HttpResponse(
                '<div class="alert alert-danger">First name is required</div>',
                status=400
            )

        user = User.objects.create_placeholder(first_name, last_name)

        # Return the user info for the autocomplete to use
        return HttpResponse(
            f'<div data-user-id="{user.pk}" data-user-name="{user.get_full_name()}">'
            f'Created: {user.get_full_name()}</div>'
        )
