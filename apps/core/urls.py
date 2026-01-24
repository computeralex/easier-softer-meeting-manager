"""
Core URL patterns.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('setup/', views.SetupWizardView.as_view(), name='setup_wizard'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('utilities/', views.UtilitiesView.as_view(), name='utilities'),
    path('utilities/backup/', views.BackupDownloadView.as_view(), name='backup_download'),
    path('utilities/restore/', views.BackupRestoreView.as_view(), name='backup_restore'),
    path('utilities/server-backup/<str:filename>/download/', views.ServerBackupDownloadView.as_view(), name='server_backup_download'),
    path('utilities/server-backup/<str:filename>/delete/', views.ServerBackupDeleteView.as_view(), name='server_backup_delete'),

    # User Management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/invite/', views.UserInviteView.as_view(), name='user_invite'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/toggle/', views.UserToggleView.as_view(), name='user_toggle'),
    path('users/<int:pk>/send-reset-email/', views.SendPasswordResetEmailView.as_view(), name='user_send_reset_email'),

    # Password Management
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # API endpoints (HTMX)
    path('api/users/search/', views.UserSearchView.as_view(), name='user_search'),
    path('api/users/quick-create/', views.QuickCreateUserView.as_view(), name='user_quick_create'),
]
