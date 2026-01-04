"""
Phone List URL configuration.
"""
from django.urls import path

from . import views

app_name = 'phone_list'

urlpatterns = [
    # Contact CRUD
    path('', views.ContactListView.as_view(), name='list'),
    path('add/', views.ContactCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.ContactUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ContactDeleteView.as_view(), name='delete'),
    path('<int:pk>/toggle/', views.ContactToggleView.as_view(), name='toggle'),

    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/regenerate/', views.RegenerateTokenView.as_view(), name='regenerate'),
    path('settings/timezone/add/', views.AddTimeZoneView.as_view(), name='add_timezone'),
    path('settings/timezone/<int:pk>/delete/', views.DeleteTimeZoneView.as_view(), name='delete_timezone'),
    path('settings/pdf/', views.UpdatePDFSettingsView.as_view(), name='update_pdf_settings'),

    # CSV Import
    path('import/', views.ImportUploadView.as_view(), name='import'),
    path('import/map/', views.ImportMapView.as_view(), name='import_map'),
    path('import/confirm/', views.ImportConfirmView.as_view(), name='import_confirm'),

    # Export
    path('export/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),
    path('export/csv/', views.ExportCSVView.as_view(), name='export_csv'),
    path('export/pdf/preview/', views.PreviewPDFView.as_view(), name='preview_pdf'),
]
