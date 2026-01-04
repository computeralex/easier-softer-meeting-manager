"""
URL configuration for positions app.
"""
from django.urls import path

from . import views

app_name = 'positions'

urlpatterns = [
    # Position management
    path('', views.PositionListView.as_view(), name='list'),
    path('add/', views.PositionCreateView.as_view(), name='create'),
    path('<int:pk>/', views.PositionDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.PositionUpdateView.as_view(), name='update'),
    path('<int:pk>/permissions/', views.PositionPermissionsView.as_view(), name='permissions'),
    path('<int:pk>/delete/', views.PositionDeleteView.as_view(), name='delete'),

    # Assignment management
    path('<int:pk>/assign/', views.AssignmentCreateView.as_view(), name='assign'),
    path('<int:pk>/end/<int:assignment_pk>/', views.EndTermView.as_view(), name='end_term'),
]
