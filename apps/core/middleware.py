"""
Core middleware.
"""
from django.shortcuts import redirect
from django.urls import reverse

from .models import MeetingConfig


class SetupWizardMiddleware:
    """
    Middleware to redirect to setup wizard if setup is not complete.

    Skips redirect if:
    - User is not authenticated
    - Setup is already completed or dismissed
    - User has skipped setup for this session
    - Already on the setup wizard page
    - On login/logout/password reset pages
    - On static/media files
    - On admin pages
    """

    EXEMPT_URLS = [
        'core:setup_wizard',
        'core:logout',
        'core:password_reset',
        'core:password_reset_done',
        'core:password_reset_confirm',
        'core:password_reset_complete',
        'website:login',
        'website:home',
        'admin:index',
    ]

    EXEMPT_PREFIXES = [
        '/admin/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Skip for exempt URL prefixes
        for prefix in self.EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return self.get_response(request)

        # Skip if setup skipped for this session
        if request.session.get('setup_skipped'):
            return self.get_response(request)

        # Check setup status
        config = MeetingConfig.get_instance()

        # Skip if setup is completed or dismissed
        if config.setup_status in ('completed', 'dismissed'):
            return self.get_response(request)

        # Skip if already on setup wizard
        if request.path == reverse('core:setup_wizard'):
            return self.get_response(request)

        # Skip for other exempt URLs
        for url_name in self.EXEMPT_URLS:
            try:
                if request.path == reverse(url_name):
                    return self.get_response(request)
            except:
                pass

        # Redirect to setup wizard
        return redirect('core:setup_wizard')
