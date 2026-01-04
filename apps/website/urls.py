"""
Website public URL configuration.

Public-facing pages (no auth required). These are mounted at the root of the site.

Admin URLs are in urls_admin.py, mounted at /dashboard/website/.
"""
from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    # Public home page
    path('', views.HomeView.as_view(), name='home'),

    # Public module pages
    path('format/', views.PublicFormatView.as_view(), name='format'),
    path('readings/', views.PublicReadingsView.as_view(), name='readings'),
    path('readings/<slug:slug>/', views.PublicReadingDetailView.as_view(), name='reading_detail'),
    path('phone-list/', views.PublicPhoneListView.as_view(), name='phone_list'),
    path('service/', views.PublicServiceView.as_view(), name='service'),
    path('treasurer/', views.PublicTreasurerView.as_view(), name='treasurer'),
    path('treasurer/<int:pk>/', views.PublicTreasurerDetailView.as_view(), name='treasurer_detail'),

    # CMS pages
    path('pages/<slug:slug>/', views.CMSPageView.as_view(), name='page'),

    # Login page (styled for public site)
    path('login/', views.PublicLoginView.as_view(), name='login'),
]
