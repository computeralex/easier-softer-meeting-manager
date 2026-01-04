"""
Public Meeting Format URL configuration (no auth required).
"""
from django.urls import path

from . import views

app_name = 'format_public'

urlpatterns = [
    path('', views.PublicFormatView.as_view(), name='view'),
    path('print/', views.PublicPrintView.as_view(), name='print'),
]
