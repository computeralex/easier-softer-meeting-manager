from django.contrib import admin
from .models import (
    Meeting, TreasurerSettings, ExpenseCategory,
    DisbursementSplit, DisbursementSplitItem,
    TreasurerRecord, TreasurerReport, RecurringExpense
)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(TreasurerSettings)
class TreasurerSettingsAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'prudent_reserve', 'starting_balance']
    list_select_related = ['meeting']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'meeting', 'is_disbursement', 'is_active']
    list_filter = ['is_disbursement', 'is_active', 'meeting']
    search_fields = ['name']


class DisbursementSplitItemInline(admin.TabularInline):
    model = DisbursementSplitItem
    extra = 1


@admin.register(DisbursementSplit)
class DisbursementSplitAdmin(admin.ModelAdmin):
    list_display = ['name', 'meeting', 'is_default']
    list_filter = ['is_default', 'meeting']
    inlines = [DisbursementSplitItemInline]


@admin.register(TreasurerRecord)
class TreasurerRecordAdmin(admin.ModelAdmin):
    list_display = ['date', 'meeting', 'type', 'amount', 'description', 'category']
    list_filter = ['type', 'meeting', 'category', 'date']
    search_fields = ['description', 'notes']
    date_hierarchy = 'date'
    list_select_related = ['meeting', 'category']


@admin.register(TreasurerReport)
class TreasurerReportAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'meeting', 'start_date', 'end_date', 'net_amount', 'is_archived']
    list_filter = ['is_archived', 'meeting']
    date_hierarchy = 'report_date'


@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'meeting', 'amount', 'frequency', 'next_due_date', 'is_active']
    list_filter = ['frequency', 'is_active', 'meeting']
