"""
Phone List admin configuration.
"""
from django.contrib import admin

from .models import TimeZone, PhoneListConfig, Contact


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    list_display = ['code', 'display_name', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'code']


@admin.register(PhoneListConfig)
class PhoneListConfigAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'is_active', 'share_token', 'updated_at']
    readonly_fields = ['share_token', 'created_at', 'updated_at']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'is_active', 'display_order']
    list_filter = ['meeting', 'is_active', 'available_to_sponsor']
    search_fields = ['name', 'phone', 'email']
    list_editable = ['is_active', 'display_order']
    ordering = ['display_order', 'name']
