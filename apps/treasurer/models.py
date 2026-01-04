"""
Treasurer module models.
Handles financial management for 12-step meeting groups.
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Meeting(models.Model):
    """
    Represents a meeting group for multi-meeting support.
    A treasurer can manage finances for multiple meetings.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TreasurerSettings(models.Model):
    """
    Settings for treasurer functionality per meeting.
    """
    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='treasurer_settings'
    )
    prudent_reserve = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount to keep in reserve for group security"
    )
    starting_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Initial balance when tracking began"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Treasurer Settings"
        verbose_name_plural = "Treasurer Settings"

    def __str__(self):
        return f"Settings for {self.meeting.name}"

    @property
    def is_configured(self) -> bool:
        """Check if initial setup has been completed."""
        return self.starting_balance != Decimal('0.00') or self.prudent_reserve != Decimal('0.00')


class IncomeCategory(models.Model):
    """
    Income categories for categorizing income transactions.
    Default is "7th Tradition", but can include others like "Bank Interest".
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='income_categories'
    )
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(
        default=False,
        help_text="Default category for new income (typically 7th Tradition)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Income Category"
        verbose_name_plural = "Income Categories"
        unique_together = ['meeting', 'name']
        ordering = ['name']

    def __str__(self):
        suffix = ' (Default)' if self.is_default else ''
        return f"{self.name}{suffix}"

    def save(self, *args, **kwargs):
        # Ensure only one default per meeting
        if self.is_default:
            IncomeCategory.objects.filter(
                meeting=self.meeting,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ExpenseCategory(models.Model):
    """
    Custom expense categories for categorizing transactions.
    Supports both regular expenses and disbursement categories.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='expense_categories'
    )
    name = models.CharField(max_length=255)
    is_disbursement = models.BooleanField(
        default=False,
        help_text="Whether this is a disbursement category (triggers split calculation)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
        unique_together = ['meeting', 'name']
        ordering = ['name']

    def __str__(self):
        suffix = ' (Disbursement)' if self.is_disbursement else ''
        return f"{self.name}{suffix}"


class DisbursementSplit(models.Model):
    """
    Configuration for splitting disbursement amounts.
    e.g., 60% District, 30% Area, 10% World Service
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='disbursement_splits'
    )
    name = models.CharField(max_length=255, help_text="Configuration name, e.g., 'Standard Split'")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Disbursement Split"
        verbose_name_plural = "Disbursement Splits"
        ordering = ['name']

    def __str__(self):
        suffix = ' (Default)' if self.is_default else ''
        return f"{self.name}{suffix}"

    def save(self, *args, **kwargs):
        # Ensure only one default per meeting
        if self.is_default:
            DisbursementSplit.objects.filter(
                meeting=self.meeting,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def calculate_splits(self, amount: Decimal) -> list:
        """
        Calculate split amounts for a given total.

        Args:
            amount: The total amount to split

        Returns:
            List of dicts with name, percentage, and calculated amount
        """
        return [
            {
                'name': item.name,
                'percentage': item.percentage,
                'amount': (amount * item.percentage / Decimal('100')).quantize(Decimal('0.01'))
            }
            for item in self.items.all()
        ]


class DisbursementSplitItem(models.Model):
    """Individual split item within a disbursement split configuration."""
    split = models.ForeignKey(
        DisbursementSplit,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=255, help_text="e.g., 'District', 'Area', 'World Service'")
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name}: {self.percentage}%"


class RecurringExpense(models.Model):
    """
    Recurring expense template for expenses like rent that repeat monthly.
    """
    class Frequency(models.TextChoices):
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        YEARLY = 'yearly', 'Yearly'

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='recurring_expenses'
    )
    description = models.CharField(max_length=500)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)
    next_due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['next_due_date']

    def __str__(self):
        return f"{self.description} ({self.get_frequency_display()})"


class TreasurerRecord(models.Model):
    """
    Individual income or expense transaction.
    The core transaction record for all financial tracking.
    """
    class RecordType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='treasurer_records'
    )
    date = models.DateField()
    type = models.CharField(max_length=10, choices=RecordType.choices)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.CharField(max_length=500, blank=True)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expense_records',
        help_text="Category for expense transactions"
    )
    income_category = models.ForeignKey(
        IncomeCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='income_records',
        help_text="Category for income transactions"
    )
    notes = models.TextField(blank=True)

    # For tracking disbursement split records
    parent_record = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='split_records',
        help_text="Parent record if this is a split disbursement"
    )
    split_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of the split (e.g., 'District') if part of a disbursement"
    )

    # Receipt file (image or PDF)
    receipt = models.FileField(
        upload_to='receipts/%Y/%m/',
        blank=True,
        null=True,
        help_text="Receipt image (JPG, PNG) or PDF"
    )

    # From recurring expense
    recurring_expense = models.ForeignKey(
        RecurringExpense,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_records'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['meeting', 'date']),
            models.Index(fields=['meeting', 'type']),
        ]

    def __str__(self):
        sign = '+' if self.type == self.RecordType.INCOME else '-'
        return f"{self.date}: {sign}${self.amount} - {self.description}"

    @property
    def is_split_child(self) -> bool:
        """Check if this record is part of a disbursement split."""
        return self.parent_record is not None


class TreasurerReport(models.Model):
    """
    Business meeting financial report for a specific period.
    Captures a snapshot of finances for reporting.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='treasurer_reports'
    )
    report_date = models.DateField(
        default=timezone.now,
        help_text="Date the report was generated"
    )
    start_date = models.DateField(help_text="First day of the report period")
    end_date = models.DateField(help_text="Last day of the report period")

    # Calculated totals (stored for historical accuracy)
    total_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_expenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Snapshot of settings at report time
    prudent_reserve = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    ending_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    available_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    is_archived = models.BooleanField(
        default=False,
        help_text="Archived reports are locked and not used for next period calculation"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-report_date', '-end_date']
        indexes = [
            models.Index(fields=['meeting', 'is_archived']),
            models.Index(fields=['meeting', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return f"Report {self.start_date} to {self.end_date}"

    def recalculate_totals(self) -> None:
        """
        Recalculate report totals from transactions.
        Used when transactions are added/modified within the period.
        """
        from django.db.models import Sum, Q
        from django.db.models.functions import Coalesce

        records = TreasurerRecord.objects.filter(
            meeting=self.meeting,
            date__gte=self.start_date,
            date__lte=self.end_date,
            parent_record__isnull=True  # Don't double-count split children
        )

        income = records.filter(type=TreasurerRecord.RecordType.INCOME).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total']

        expenses = records.filter(type=TreasurerRecord.RecordType.EXPENSE).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total']

        self.total_income = income
        self.total_expenses = expenses
        self.net_amount = income - expenses
        self.save(update_fields=['total_income', 'total_expenses', 'net_amount', 'updated_at'])
