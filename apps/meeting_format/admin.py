from django.contrib import admin

from .models import FormatBlock, BlockVariation, VariationSchedule, FormatModuleConfig


@admin.register(FormatBlock)
class FormatBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting', 'order', 'is_active']
    list_filter = ['meeting', 'is_active']
    ordering = ['meeting', 'order']


@admin.register(BlockVariation)
class BlockVariationAdmin(admin.ModelAdmin):
    list_display = ['name', 'block', 'order', 'is_default', 'is_active']
    list_filter = ['block__meeting', 'is_default', 'is_active']
    ordering = ['block', 'order']


@admin.register(VariationSchedule)
class VariationScheduleAdmin(admin.ModelAdmin):
    list_display = ['variation', 'schedule_type', 'occurrence', 'weekday', 'specific_date']
    list_filter = ['schedule_type', 'variation__block__meeting']


@admin.register(FormatModuleConfig)
class FormatModuleConfigAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'public_enabled', 'share_token']
    list_filter = ['public_enabled']
