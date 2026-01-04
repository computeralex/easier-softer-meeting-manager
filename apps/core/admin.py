from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ServicePosition, MeetingConfig


@admin.register(ServicePosition)
class ServicePositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'order']
    ordering = ['order', 'name']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'is_active', 'is_staff', 'get_positions']
    list_filter = ['is_active', 'is_staff', 'positions']
    search_fields = ['email', 'name']
    ordering = ['email']
    filter_horizontal = ['positions', 'groups', 'user_permissions']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name',)}),
        ('Service Positions', {'fields': ('positions',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'positions'),
        }),
    )

    def get_positions(self, obj):
        return ', '.join(obj.position_names) or '-'
    get_positions.short_description = 'Positions'


@admin.register(MeetingConfig)
class MeetingConfigAdmin(admin.ModelAdmin):
    list_display = ['meeting_name', 'meeting_day', 'meeting_time']

    def has_add_permission(self, request):
        # Only allow one instance
        return not MeetingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
