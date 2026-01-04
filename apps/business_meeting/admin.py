from django.contrib import admin
from .models import BusinessMeetingFormat, BusinessMeeting


@admin.register(BusinessMeetingFormat)
class BusinessMeetingFormatAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at']


@admin.register(BusinessMeeting)
class BusinessMeetingAdmin(admin.ModelAdmin):
    list_display = ['date', 'meeting', 'created_at', 'created_by']
    list_filter = ['meeting', 'date']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
