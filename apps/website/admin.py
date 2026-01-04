"""
Website admin configuration.
"""
from django.contrib import admin
from .models import WebsiteModuleConfig, WebsitePage


@admin.register(WebsiteModuleConfig)
class WebsiteModuleConfigAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'home_page_type', 'public_format_enabled', 'public_readings_enabled']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WebsitePage)
class WebsitePageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'show_in_nav', 'nav_order', 'meeting']
    list_filter = ['is_published', 'show_in_nav', 'meeting']
    search_fields = ['title', 'slug', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
