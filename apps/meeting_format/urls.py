"""
Meeting Format URL configuration (admin views).
"""
from django.urls import path

from . import views

app_name = 'meeting_format'

urlpatterns = [
    # Block CRUD
    path('', views.BlockListView.as_view(), name='block_list'),
    path('blocks/add/', views.BlockCreateView.as_view(), name='block_create'),
    path('blocks/<int:pk>/edit/', views.BlockUpdateView.as_view(), name='block_update'),
    path('blocks/<int:pk>/delete/', views.BlockDeleteView.as_view(), name='block_delete'),
    path('blocks/reorder/', views.BlockReorderView.as_view(), name='block_reorder'),

    # Variation CRUD
    path('blocks/<int:block_pk>/variations/add/', views.VariationCreateView.as_view(), name='variation_create'),
    path('variations/<int:pk>/edit/', views.VariationUpdateView.as_view(), name='variation_update'),
    path('variations/<int:pk>/delete/', views.VariationDeleteView.as_view(), name='variation_delete'),

    # Schedule CRUD
    path('variations/<int:variation_pk>/schedule/add/', views.ScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<int:pk>/delete/', views.ScheduleDeleteView.as_view(), name='schedule_delete'),

    # Meeting Type CRUD
    path('types/', views.MeetingTypeListView.as_view(), name='meeting_type_list'),
    path('types/add/', views.MeetingTypeCreateView.as_view(), name='meeting_type_create'),
    path('types/<int:pk>/edit/', views.MeetingTypeUpdateView.as_view(), name='meeting_type_update'),
    path('types/<int:pk>/delete/', views.MeetingTypeDeleteView.as_view(), name='meeting_type_delete'),
    path('types/select/', views.SelectMeetingTypeView.as_view(), name='select_meeting_type'),

    # Settings
    path('settings/', views.FormatSettingsView.as_view(), name='settings'),
]
