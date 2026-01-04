"""
Business Meeting URL configuration.
"""
from django.urls import path
from . import views

app_name = 'business_meeting'

urlpatterns = [
    # Format editor
    path('format/', views.FormatEditView.as_view(), name='format_edit'),

    # Meeting CRUD
    path('', views.MeetingListView.as_view(), name='meeting_list'),
    path('new/', views.MeetingCreateView.as_view(), name='meeting_create'),
    path('<int:pk>/', views.MeetingDetailView.as_view(), name='meeting_detail'),
    path('<int:pk>/edit/', views.MeetingUpdateView.as_view(), name='meeting_update'),
    path('<int:pk>/delete/', views.MeetingDeleteView.as_view(), name='meeting_delete'),
]
