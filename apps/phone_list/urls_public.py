"""
Public Phone List URL configuration (no auth required).
"""
from django.urls import path

from . import views

app_name = 'phone_list_public'

urlpatterns = [
    path('', views.PublicPhoneListView.as_view(), name='view'),
]
