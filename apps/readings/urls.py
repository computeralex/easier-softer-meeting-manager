"""
Readings URL configuration.
"""
from django.urls import path

from . import views

app_name = 'readings'

urlpatterns = [
    # Reading CRUD
    path('', views.ReadingListView.as_view(), name='list'),
    path('add/', views.ReadingCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.ReadingUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ReadingDeleteView.as_view(), name='delete'),

    # Category CRUD
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Reorder
    path('reorder/', views.ReorderView.as_view(), name='reorder'),
    path('reorder/categories/', views.ReorderCategoriesView.as_view(), name='reorder_categories'),
    path('reorder/readings/', views.ReorderReadingsView.as_view(), name='reorder_readings'),

    # Import
    path('import/', views.ImportView.as_view(), name='import'),

    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/regenerate/', views.RegenerateTokenView.as_view(), name='regenerate'),
    path('settings/font/', views.FontSettingsView.as_view(), name='settings_font'),
]
