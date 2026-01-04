"""
Public Readings URL configuration (no auth required).
"""
from django.urls import path

from . import views

app_name = 'readings_public'

urlpatterns = [
    path('', views.PublicReadingListView.as_view(), name='list'),
    path('<slug:slug>/', views.PublicReadingDetailView.as_view(), name='detail'),
]
