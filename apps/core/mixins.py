"""
Permission mixins for views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class PositionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires a specific service position to access the view.

    Usage:
        class MyView(PositionRequiredMixin, View):
            required_position = 'treasurer'
    """
    required_position = None
    required_positions = None  # Alternative: list of acceptable positions

    def test_func(self):
        # Superusers always have access
        if self.request.user.is_superuser:
            return True
        if self.required_positions:
            return self.request.user.has_any_position(self.required_positions)
        if self.required_position:
            return self.request.user.has_position(self.required_position)
        return True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have the required service position.")
        return super().handle_no_permission()


class TreasurerRequiredMixin(PositionRequiredMixin):
    """Convenience mixin for treasurer-only views."""
    required_position = 'treasurer'


class SecretaryRequiredMixin(PositionRequiredMixin):
    """Convenience mixin for secretary-only views."""
    required_position = 'secretary'


class ServicePositionRequiredMixin(PositionRequiredMixin):
    """Mixin for views accessible by any service position holder."""
    required_positions = ['treasurer', 'secretary', 'literature', 'gsr']

    def test_func(self):
        # Superusers always have access
        if self.request.user.is_superuser:
            return True
        # Any authenticated user with at least one position can access
        return self.request.user.is_service_position_holder


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires superuser/admin access."""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Administrator access required.")
        return super().handle_no_permission()
