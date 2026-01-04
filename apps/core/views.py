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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import management
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, CreateView, UpdateView, DeleteView

from .mixins import ServicePositionRequiredMixin
from .models import MeetingConfig, User, ServicePosition, PositionAssignment
from .forms import (
    MeetingConfigForm, UserProfileForm, UserForm, UserInviteForm, PasswordChangeFormStyled
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


class LoginView(auth_views.LoginView):
    """Custom login view."""
    template_name = 'core/login.html'
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    """Custom logout view."""
    pass


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


class BackupDownloadView(ServicePositionRequiredMixin, View):
    """Download a backup file (JSON export of all data). Restricted to service positions."""

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


class BackupRestoreView(ServicePositionRequiredMixin, View):
    """Restore data from uploaded backup file. Restricted to service positions."""

    # Models that cannot be restored via backup (security-sensitive)
    BLOCKED_MODELS = {
        'core.user',
        'core.serviceposition',
        'core.positionassignment',
        'auth.user',
        'auth.group',
        'auth.permission',
        'admin.logentry',
        'sessions.session',
        'axes.accessattempt',
        'axes.accesslog',
        'axes.accessfailurelog',
    }

    def post(self, request):
        if 'backup_file' not in request.FILES:
            messages.error(request, 'No file uploaded.')
            return redirect('core:utilities')

        backup_file = request.FILES['backup_file']

        # Validate it's JSON
        if not backup_file.name.endswith('.json'):
            messages.error(request, 'Please upload a .json backup file.')
            return redirect('core:utilities')

        try:
            # Read and validate JSON
            content = backup_file.read().decode('utf-8')
            data = json.loads(content)

            # Validate backup structure and check for blocked models
            if not isinstance(data, list):
                messages.error(request, 'Invalid backup format: expected a list.')
                return redirect('core:utilities')

            blocked_found = set()
            for item in data:
                if not isinstance(item, dict) or 'model' not in item:
                    messages.error(request, 'Invalid backup format: malformed entry.')
                    return redirect('core:utilities')
                model_name = item['model'].lower()
                if model_name in self.BLOCKED_MODELS:
                    blocked_found.add(item['model'])

            if blocked_found:
                messages.error(
                    request,
                    f'Backup contains restricted models that cannot be restored: {", ".join(sorted(blocked_found))}. '
                    f'User and permission data must be managed through the admin interface.'
                )
                return redirect('core:utilities')

            # Save to temp file and load
            temp_path = Path(settings.BASE_DIR) / 'backups' / 'temp_restore.json'
            temp_path.parent.mkdir(exist_ok=True)
            temp_path.write_text(content)

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


class ServerBackupDownloadView(ServicePositionRequiredMixin, View):
    """Download a specific backup file from the server. Restricted to service positions."""

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


class ServerBackupDeleteView(ServicePositionRequiredMixin, View):
    """Delete a specific backup file from the server. Restricted to service positions."""

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


class UserCreateView(ServicePositionRequiredMixin, CreateView):
    """Create a new user."""
    model = User
    form_class = UserForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('core:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add User'
        return context

    def form_valid(self, form):
        # Generate a random password for new users
        password = secrets.token_urlsafe(12)
        user = form.save(commit=False)
        user.set_password(password)
        user.save()
        form.save_m2m()  # Save positions

        messages.success(
            self.request,
            f'User "{user.email}" created. Temporary password: {password}'
        )
        return redirect(self.success_url)


class UserUpdateView(ServicePositionRequiredMixin, UpdateView):
    """Edit an existing user."""
    model = User
    form_class = UserForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('core:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit User: {self.object.email}'
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

        # Generate random password
        password = secrets.token_urlsafe(12)

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
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

        if send_email_flag:
            # Send welcome email
            login_url = self.request.build_absolute_uri(reverse('core:login'))
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
