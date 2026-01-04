"""
URL configuration for Meeting Manager.

URL structure:
- / -> Public home page (format or CMS page)
- /format/ -> Public meeting format
- /readings/ -> Public readings list
- /phone-list/ -> Public phone list (if enabled)
- /pages/{slug}/ -> CMS pages

Admin URLs (login required):
- /dashboard/ -> Admin dashboard
- /dashboard/settings/ -> Global settings
- /dashboard/users/ -> User management
- /dashboard/treasurer/ -> Treasurer admin
- /dashboard/format/ -> Format admin
- etc.

Token URLs (alternative private sharing):
- /f/{token}/ -> Public format via token
- /r/{token}/ -> Public readings via token
- /p/{token}/ -> Public phone list via token
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Admin dashboard and core (authenticated) - under /dashboard/
    path('dashboard/', include('apps.core.urls')),

    # Module admin apps (authenticated) - under /dashboard/
    path('dashboard/positions/', include('apps.positions.urls')),
    path('dashboard/treasurer/', include('apps.treasurer.urls')),
    path('dashboard/phone-list/', include('apps.phone_list.urls')),
    path('dashboard/readings/', include('apps.readings.urls')),
    path('dashboard/format/', include('apps.meeting_format.urls')),
    path('dashboard/business/', include('apps.business_meeting.urls')),
    path('dashboard/website/', include('apps.website.urls_admin')),

    # Token URLs (alternative private sharing)
    path('f/<str:token>/', include('apps.meeting_format.urls_public')),
    path('r/<str:token>/', include('apps.readings.urls_public')),
    path('p/<str:token>/', include('apps.phone_list.urls_public')),

    # Website public pages (MUST BE LAST - catches unmatched routes)
    path('', include('apps.website.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
