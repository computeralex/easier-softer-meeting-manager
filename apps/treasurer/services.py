"""
Business logic for treasurer operations.
Keeps views thin and logic testable.
"""
import io
import json
import zipfile
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Tuple, List, Any

from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.core.serializers.json import DjangoJSONEncoder

from .models import (
    Meeting, TreasurerSettings, TreasurerRecord, TreasurerReport,
    ExpenseCategory, IncomeCategory, DisbursementSplit, DisbursementSplitItem, RecurringExpense
)


class TreasurerService:
    """Service class for treasurer business logic."""

    def __init__(self, meeting: Meeting):
        self.meeting = meeting

    def get_or_create_settings(self) -> Tuple[TreasurerSettings, bool]:
        """Get or create treasurer settings for meeting."""
        return TreasurerSettings.objects.get_or_create(meeting=self.meeting)

    def ensure_default_income_categories(self) -> None:
        """Ensure default income categories exist for the meeting."""
        # Create "7th Tradition" as the default if no income categories exist
        if not IncomeCategory.objects.filter(meeting=self.meeting).exists():
            IncomeCategory.objects.create(
                meeting=self.meeting,
                name='7th Tradition',
                is_default=True
            )

    def get_current_balance(self) -> Decimal:
        """
        Calculate current balance.
        Current Balance = Starting Balance + SUM(income) - SUM(expenses)
        """
        settings, _ = self.get_or_create_settings()

        # Only count parent records (not split children) to avoid double-counting
        net = TreasurerRecord.objects.filter(
            meeting=self.meeting,
            parent_record__isnull=True
        ).aggregate(
            income=Coalesce(
                Sum('amount', filter=Q(type=TreasurerRecord.RecordType.INCOME)),
                Decimal('0.00')
            ),
            expenses=Coalesce(
                Sum('amount', filter=Q(type=TreasurerRecord.RecordType.EXPENSE)),
                Decimal('0.00')
            )
        )

        return settings.starting_balance + net['income'] - net['expenses']

    def get_available_funds(self) -> Decimal:
        """
        Calculate available funds.
        Available Funds = Current Balance - Prudent Reserve
        """
        settings, _ = self.get_or_create_settings()
        return self.get_current_balance() - settings.prudent_reserve

    def get_summary(self) -> Dict:
        """Get complete financial summary."""
        settings, _ = self.get_or_create_settings()

        # Get totals in one query
        totals = TreasurerRecord.objects.filter(
            meeting=self.meeting,
            parent_record__isnull=True
        ).aggregate(
            total_income=Coalesce(
                Sum('amount', filter=Q(type=TreasurerRecord.RecordType.INCOME)),
                Decimal('0.00')
            ),
            total_expenses=Coalesce(
                Sum('amount', filter=Q(type=TreasurerRecord.RecordType.EXPENSE)),
                Decimal('0.00')
            )
        )

        current_balance = settings.starting_balance + totals['total_income'] - totals['total_expenses']

        return {
            'current_balance': current_balance,
            'available_funds': current_balance - settings.prudent_reserve,
            'prudent_reserve': settings.prudent_reserve,
            'starting_balance': settings.starting_balance,
            'total_income': totals['total_income'],
            'total_expenses': totals['total_expenses'],
            'is_configured': settings.is_configured,
        }

    def get_recent_records(self, limit: int = 10) -> List[TreasurerRecord]:
        """Get recent transactions."""
        return TreasurerRecord.objects.filter(
            meeting=self.meeting,
            parent_record__isnull=True  # Don't show split children
        ).select_related('category')[:limit]

    @transaction.atomic
    def add_income(
        self,
        date: date,
        amount: Decimal,
        description: str = '7th Tradition',
        income_category=None,
        notes: str = '',
        created_by=None
    ) -> TreasurerRecord:
        """Add an income record (typically 7th Tradition)."""
        return TreasurerRecord.objects.create(
            meeting=self.meeting,
            date=date,
            type=TreasurerRecord.RecordType.INCOME,
            amount=amount,
            description=description,
            income_category=income_category,
            notes=notes,
            created_by_id=created_by.pk if created_by else None,
        )

    @transaction.atomic
    def add_expense(
        self,
        date: date,
        amount: Decimal,
        description: str,
        category: Optional[ExpenseCategory] = None,
        notes: str = '',
        disbursement_split: Optional[DisbursementSplit] = None,
        receipt=None,
        created_by=None
    ) -> List[TreasurerRecord]:
        """
        Add an expense record.
        Handles disbursement splits automatically.

        Returns:
            List of created records (multiple if disbursement split)
        """
        created_records = []

        if disbursement_split:
            # Create parent record (with full amount for reference)
            parent = TreasurerRecord.objects.create(
                meeting=self.meeting,
                date=date,
                type=TreasurerRecord.RecordType.EXPENSE,
                amount=amount,
                description=description,
                category=category,
                notes=notes,
                receipt=receipt,
                created_by_id=created_by.pk if created_by else None,
            )
            created_records.append(parent)

            # Create split child records
            splits = disbursement_split.calculate_splits(amount)
            for split in splits:
                child = TreasurerRecord.objects.create(
                    meeting=self.meeting,
                    date=date,
                    type=TreasurerRecord.RecordType.EXPENSE,
                    amount=split['amount'],
                    description=f"{description} - {split['name']}",
                    category=category,
                    notes=notes,
                    parent_record=parent,
                    split_name=split['name'],
                    created_by_id=created_by.pk if created_by else None,
                )
                created_records.append(child)
        else:
            # Regular single record
            record = TreasurerRecord.objects.create(
                meeting=self.meeting,
                date=date,
                type=TreasurerRecord.RecordType.EXPENSE,
                amount=amount,
                description=description,
                category=category,
                notes=notes,
                receipt=receipt,
                created_by_id=created_by.pk if created_by else None,
            )
            created_records.append(record)

        return created_records

    def check_report_conflict(self, transaction_date: date) -> Optional[TreasurerReport]:
        """
        Check if a transaction date conflicts with an existing report period.

        Returns:
            The conflicting report, or None if no conflict
        """
        return TreasurerReport.objects.filter(
            meeting=self.meeting,
            start_date__lte=transaction_date,
            end_date__gte=transaction_date,
            is_archived=False
        ).first()

    def get_next_report_period(self) -> Tuple[date, date]:
        """
        Get the next available report period.
        Start: Day after last non-archived report ended
        End: Today
        """
        last_report = TreasurerReport.objects.filter(
            meeting=self.meeting,
            is_archived=False
        ).order_by('-end_date').first()

        if last_report:
            start_date = last_report.end_date + timedelta(days=1)
        else:
            # Get first record date or today
            first_record = TreasurerRecord.objects.filter(
                meeting=self.meeting
            ).order_by('date').first()
            start_date = first_record.date if first_record else date.today()

        return start_date, date.today()

    def check_period_overlap(
        self,
        start_date: date,
        end_date: date,
        exclude_report: Optional[TreasurerReport] = None
    ) -> bool:
        """Check if a period overlaps with existing reports."""
        queryset = TreasurerReport.objects.filter(meeting=self.meeting)

        if exclude_report:
            queryset = queryset.exclude(pk=exclude_report.pk)

        return queryset.filter(
            Q(start_date__lte=start_date, end_date__gte=start_date) |
            Q(start_date__lte=end_date, end_date__gte=end_date) |
            Q(start_date__gte=start_date, end_date__lte=end_date)
        ).exists()

    def get_period_totals(self, start_date: date, end_date: date) -> Dict:
        """Get income/expense totals for a period."""
        records = TreasurerRecord.objects.filter(
            meeting=self.meeting,
            date__gte=start_date,
            date__lte=end_date,
            parent_record__isnull=True
        )

        totals = records.aggregate(
            income=Coalesce(
                Sum('amount', filter=Q(type=TreasurerRecord.RecordType.INCOME)),
                Decimal('0.00')
            ),
            expenses=Coalesce(
                Sum('amount', filter=Q(type=TreasurerRecord.RecordType.EXPENSE)),
                Decimal('0.00')
            )
        )

        return {
            'total_income': totals['income'],
            'total_expenses': totals['expenses'],
            'net_amount': totals['income'] - totals['expenses'],
        }

    @transaction.atomic
    def create_report(
        self,
        start_date: date,
        end_date: date,
        created_by=None
    ) -> TreasurerReport:
        """
        Create a new business meeting report for the specified period.
        """
        settings, _ = self.get_or_create_settings()
        totals = self.get_period_totals(start_date, end_date)
        current_balance = self.get_current_balance()

        report = TreasurerReport.objects.create(
            meeting=self.meeting,
            report_date=date.today(),
            start_date=start_date,
            end_date=end_date,
            total_income=totals['total_income'],
            total_expenses=totals['total_expenses'],
            net_amount=totals['net_amount'],
            prudent_reserve=settings.prudent_reserve,
            ending_balance=current_balance,
            available_balance=current_balance - settings.prudent_reserve,
            created_by_id=created_by.pk if created_by else None,
        )

        return report

    def archive_report(self, report: TreasurerReport) -> None:
        """Archive a report, locking it from period calculations."""
        report.is_archived = True
        report.save(update_fields=['is_archived', 'updated_at'])

    def get_year_summary(self, year: int) -> Dict:
        """Get annual summary for GSR reports."""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        totals = self.get_period_totals(start_date, end_date)

        # Get category breakdown
        expense_by_category = TreasurerRecord.objects.filter(
            meeting=self.meeting,
            date__gte=start_date,
            date__lte=end_date,
            type=TreasurerRecord.RecordType.EXPENSE,
            parent_record__isnull=True
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        return {
            'year': year,
            **totals,
            'expense_by_category': list(expense_by_category),
        }
