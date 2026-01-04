"""
Treasurer module URL patterns.
All URLs are namespaced under 'treasurer:'.
"""
from django.urls import path
from . import views

app_name = 'treasurer'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('setup/', views.SetupView.as_view(), name='setup'),

    # Records
    path('records/', views.RecordListView.as_view(), name='record_list'),
    path('records/add/', views.AddRecordView.as_view(), name='add_record'),
    path('records/<int:pk>/', views.RecordDetailView.as_view(), name='record_detail'),
    path('records/<int:pk>/edit/', views.EditRecordView.as_view(), name='edit_record'),
    path('records/<int:pk>/delete/', views.DeleteRecordView.as_view(), name='delete_record'),

    # Reports
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/create/', views.CreateReportView.as_view(), name='create_report'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/archive/', views.ArchiveReportView.as_view(), name='archive_report'),
    path('reports/<int:pk>/delete/', views.DeleteReportView.as_view(), name='delete_report'),
    path('reports/<int:pk>/pdf/', views.ReportPDFView.as_view(), name='report_pdf'),
    path('reports/<int:pk>/csv/', views.ReportCSVView.as_view(), name='report_csv'),

    # Year summary
    path('reports/year/<int:year>/', views.YearSummaryView.as_view(), name='year_summary'),

    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/categories/', views.CategoryListView.as_view(), name='categories'),
    path('settings/categories/add/', views.AddCategoryView.as_view(), name='add_category'),
    path('settings/categories/<int:pk>/delete/', views.DeleteCategoryView.as_view(), name='delete_category'),
    path('settings/income-categories/add/', views.AddIncomeCategoryView.as_view(), name='add_income_category'),
    path('settings/income-categories/<int:pk>/delete/', views.DeleteIncomeCategoryView.as_view(), name='delete_income_category'),
    path('settings/splits/', views.SplitListView.as_view(), name='splits'),
    path('settings/splits/add/', views.AddSplitView.as_view(), name='add_split'),
    path('settings/splits/<int:pk>/edit/', views.EditSplitView.as_view(), name='edit_split'),
    path('settings/splits/<int:pk>/default/', views.SetDefaultSplitView.as_view(), name='set_default_split'),
    path('settings/splits/<int:pk>/delete/', views.DeleteSplitView.as_view(), name='delete_split'),

    # Recurring expenses
    path('recurring/', views.RecurringExpenseListView.as_view(), name='recurring_list'),
    path('recurring/add/', views.AddRecurringExpenseView.as_view(), name='add_recurring'),
    path('recurring/<int:pk>/delete/', views.DeleteRecurringExpenseView.as_view(), name='delete_recurring'),

    # HTMX endpoints
    path('htmx/preview-report/', views.PreviewReportView.as_view(), name='preview_report'),
    path('htmx/calculate-split/', views.CalculateSplitView.as_view(), name='calculate_split'),
]
