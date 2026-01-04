"""
Website admin URL configuration.

These URLs are mounted under /dashboard/website/ for authenticated admin access.
Note: Uses 'website_admin' namespace to avoid conflict with public 'website' namespace.
"""
from django.urls import path
from . import views

app_name = 'website_admin'

urlpatterns = [
    # Admin dashboard - overview of pages and settings
    path('', views.WebsiteAdminView.as_view(), name='admin'),

    # CMS page management
    path('pages/', views.PageListView.as_view(), name='page_list'),
    path('pages/add/', views.PageCreateView.as_view(), name='page_create'),
    path('pages/<int:pk>/edit/', views.PageUpdateView.as_view(), name='page_update'),
    path('pages/<int:pk>/delete/', views.PageDeleteView.as_view(), name='page_delete'),

    # Puck visual editor
    path('pages/editor/', views.PuckEditorView.as_view(), name='puck_editor_new'),
    path('pages/<int:pk>/editor/', views.PuckEditorView.as_view(), name='puck_editor'),
    path('pages/<int:pk>/save-content/', views.SavePageContentView.as_view(), name='page_save_content'),

    # Image upload for Puck editor
    path('upload-image/', views.UploadImageView.as_view(), name='upload_image'),
]
