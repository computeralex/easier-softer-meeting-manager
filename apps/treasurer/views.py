"""
Treasurer views.
"""
import csv
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, DeleteView, FormView
)

from apps.core.mixins import TreasurerRequiredMixin
from .models import (
    Meeting, TreasurerSettings, TreasurerRecord, TreasurerReport,
    ExpenseCategory, IncomeCategory, DisbursementSplit, DisbursementSplitItem, RecurringExpense
)
from .services import TreasurerService
from .forms import (
    SetupForm, AddRecordForm, EditRecordForm, CreateReportForm, TreasurerSettingsForm,
    IncomeCategoryForm, CategoryForm, DisbursementSplitForm, RecurringExpenseForm
)


class MeetingMixin:
    """Mixin to get the current meeting."""

    def get_meeting(self):
        # For now, get or create first meeting
        # Multi-meeting support will add meeting selection
        meeting, _ = Meeting.objects.get_or_create(
            pk=1,
            defaults={'name': 'My Meeting'}
        )
        return meeting

    def get_service(self):
        return TreasurerService(self.get_meeting())


# ============================================================================
# Dashboard & Setup
# ============================================================================

class DashboardView(LoginRequiredMixin, MeetingMixin, TemplateView):
    """Treasurer dashboard with financial summary."""
    template_name = 'treasurer/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_service()
        # Ensure default income categories exist
        service.ensure_default_income_categories()
        context['meeting'] = self.get_meeting()
        context['summary'] = service.get_summary()
        context['recent_records'] = service.get_recent_records(10)
        context['categories'] = ExpenseCategory.objects.filter(
            meeting=self.get_meeting(), is_active=True
        )
        return context


class SetupView(TreasurerRequiredMixin, MeetingMixin, FormView):
    """Initial setup for treasurer settings."""
    template_name = 'treasurer/setup.html'
    form_class = SetupForm
    success_url = reverse_lazy('treasurer:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        settings, _ = self.get_service().get_or_create_settings()
        kwargs['instance'] = settings
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Treasurer settings saved successfully.')
        return super().form_valid(form)


# ============================================================================
# Records
# ============================================================================

class AddRecordView(TreasurerRequiredMixin, MeetingMixin, FormView):
    """Add income or expense record."""
    template_name = 'treasurer/add_record.html'
    form_class = AddRecordForm
    success_url = reverse_lazy('treasurer:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meeting'] = self.get_meeting()
        context['categories'] = ExpenseCategory.objects.filter(
            meeting=self.get_meeting(), is_active=True
        )
        context['splits'] = DisbursementSplit.objects.filter(
            meeting=self.get_meeting()
        ).prefetch_related('items')
        return context

    def form_valid(self, form):
        service = self.get_service()
        data = form.cleaned_data

        if data['record_type'] == 'income':
            income_category = data.get('income_category')
            # Use category name as description if no description provided
            description = data.get('description')
            if not description and income_category:
                description = income_category.name
            elif not description:
                description = '7th Tradition'

            service.add_income(
                date=data['date'],
                amount=data['amount'],
                description=description,
                income_category=income_category,
                notes=data.get('notes', ''),
                created_by=self.request.user
            )
            messages.success(self.request, f"Income of ${data['amount']} recorded.")
        else:
            service.add_expense(
                date=data['date'],
                amount=data['amount'],
                description=data['description'],
                category=data.get('category'),
                notes=data.get('notes', ''),
                disbursement_split=data.get('disbursement_split'),
                receipt=data.get('receipt'),
                created_by=self.request.user
            )
            messages.success(self.request, f"Expense of ${data['amount']} recorded.")

        return super().form_valid(form)


class RecordListView(LoginRequiredMixin, MeetingMixin, ListView):
    """List all transactions with pagination."""
    template_name = 'treasurer/record_list.html'
    context_object_name = 'records'
    paginate_by = 25

    def get_queryset(self):
        return TreasurerRecord.objects.filter(
            meeting=self.get_meeting(),
            parent_record__isnull=True
        ).select_related('category').order_by('-date', '-pk')


class RecordDetailView(LoginRequiredMixin, MeetingMixin, DetailView):
    """View record details."""
    template_name = 'treasurer/record_detail.html'
    context_object_name = 'record'

    def get_queryset(self):
        return TreasurerRecord.objects.filter(meeting=self.get_meeting())


class EditRecordView(TreasurerRequiredMixin, MeetingMixin, FormView):
    """Edit an existing transaction."""
    template_name = 'treasurer/edit_record.html'
    form_class = EditRecordForm
    success_url = reverse_lazy('treasurer:record_list')

    def get_record(self):
        if not hasattr(self, '_record'):
            self._record = get_object_or_404(
                TreasurerRecord,
                pk=self.kwargs['pk'],
                meeting=self.get_meeting(),
                parent_record__isnull=True  # Can only edit parent records
            )
        return self._record

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        kwargs['instance'] = self.get_record()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.get_record()
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Transaction updated.')
        return super().form_valid(form)


class DeleteRecordView(TreasurerRequiredMixin, MeetingMixin, DeleteView):
    """Delete a record."""
    template_name = 'treasurer/record_confirm_delete.html'
    success_url = reverse_lazy('treasurer:dashboard')
    context_object_name = 'record'

    def get_queryset(self):
        return TreasurerRecord.objects.filter(meeting=self.get_meeting())

    def form_valid(self, form):
        messages.success(self.request, 'Record deleted.')
        return super().form_valid(form)


# ============================================================================
# Reports
# ============================================================================

class ReportListView(LoginRequiredMixin, MeetingMixin, ListView):
    """List all reports."""
    template_name = 'treasurer/report_list.html'
    context_object_name = 'reports'

    def get_queryset(self):
        return TreasurerReport.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_service()
        start, end = service.get_next_report_period()
        context['next_period'] = {'start': start, 'end': end}
        context['period_totals'] = service.get_period_totals(start, end)
        return context


class CreateReportView(TreasurerRequiredMixin, MeetingMixin, FormView):
    """Create a new report."""
    template_name = 'treasurer/create_report.html'
    form_class = CreateReportForm
    success_url = reverse_lazy('treasurer:report_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def get_initial(self):
        service = self.get_service()
        start, end = service.get_next_report_period()
        return {'start_date': start, 'end_date': end}

    def form_valid(self, form):
        service = self.get_service()
        report = service.create_report(
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date'],
            created_by=self.request.user
        )
        messages.success(self.request, f'Report created for {report.start_date} to {report.end_date}.')
        return redirect('treasurer:report_detail', pk=report.pk)


class ReportDetailView(LoginRequiredMixin, MeetingMixin, DetailView):
    """View report details."""
    template_name = 'treasurer/report_detail.html'
    context_object_name = 'report'

    def get_queryset(self):
        return TreasurerReport.objects.filter(meeting=self.get_meeting())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.object
        context['records'] = TreasurerRecord.objects.filter(
            meeting=self.get_meeting(),
            date__gte=report.start_date,
            date__lte=report.end_date,
            parent_record__isnull=True
        ).select_related('category').order_by('date')
        return context


class ArchiveReportView(TreasurerRequiredMixin, MeetingMixin, View):
    """Archive a report."""

    def post(self, request, pk):
        report = get_object_or_404(
            TreasurerReport, pk=pk, meeting=self.get_meeting()
        )
        service = self.get_service()
        service.archive_report(report)
        messages.success(request, 'Report archived.')
        return redirect('treasurer:report_list')


class DeleteReportView(TreasurerRequiredMixin, MeetingMixin, DeleteView):
    """Delete a report."""
    template_name = 'treasurer/report_confirm_delete.html'
    success_url = reverse_lazy('treasurer:report_list')
    context_object_name = 'report'

    def get_queryset(self):
        return TreasurerReport.objects.filter(meeting=self.get_meeting())


class ReportPDFView(LoginRequiredMixin, MeetingMixin, View):
    """Generate PDF for report using WeasyPrint."""

    def get(self, request, pk):
        from django.template.loader import render_to_string
        from weasyprint import HTML

        meeting = self.get_meeting()
        report = get_object_or_404(TreasurerReport, pk=pk, meeting=meeting)

        records = TreasurerRecord.objects.filter(
            meeting=meeting,
            date__gte=report.start_date,
            date__lte=report.end_date,
            parent_record__isnull=True
        ).select_related('category').order_by('date')

        html_string = render_to_string('treasurer/report_pdf.html', {
            'report': report,
            'meeting': meeting,
            'records': records,
        })

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{report.start_date}_{report.end_date}.pdf"'
        return response


class ReportCSVView(LoginRequiredMixin, MeetingMixin, View):
    """Export report as CSV."""

    def get(self, request, pk):
        meeting = self.get_meeting()
        report = get_object_or_404(TreasurerReport, pk=pk, meeting=meeting)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="report_{report.start_date}_{report.end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Type', 'Description', 'Category', 'Amount', 'Notes'])

        records = TreasurerRecord.objects.filter(
            meeting=meeting,
            date__gte=report.start_date,
            date__lte=report.end_date,
            parent_record__isnull=True
        ).select_related('category').order_by('date')

        for record in records:
            writer.writerow([
                record.date,
                record.type,
                record.description,
                record.category.name if record.category else '',
                record.amount,
                record.notes
            ])

        writer.writerow([])
        writer.writerow(['', '', '', 'Total Income:', report.total_income, ''])
        writer.writerow(['', '', '', 'Total Expenses:', report.total_expenses, ''])
        writer.writerow(['', '', '', 'Net:', report.net_amount, ''])

        return response


class YearSummaryView(LoginRequiredMixin, MeetingMixin, TemplateView):
    """Annual summary for GSR reports."""
    template_name = 'treasurer/year_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        service = self.get_service()
        context['summary'] = service.get_year_summary(year)
        context['year'] = year
        return context


# ============================================================================
# Settings
# ============================================================================

class SettingsView(TreasurerRequiredMixin, View):
    """Treasurer settings - redirects to Global Settings."""

    def get(self, request):
        """Redirect to Global Settings treasury tab."""
        return redirect(f"{reverse('core:settings')}?tab=treasurer")

    def post(self, request):
        """Redirect POST to Global Settings (form handled there)."""
        return redirect(f"{reverse('core:settings')}?tab=treasurer")


class CategoryListView(LoginRequiredMixin, MeetingMixin, ListView):
    """List expense categories."""
    template_name = 'treasurer/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ExpenseCategory.objects.filter(meeting=self.get_meeting())


class AddCategoryView(TreasurerRequiredMixin, MeetingMixin, CreateView):
    """Add expense category."""
    template_name = 'treasurer/category_form.html'
    form_class = CategoryForm

    def get_success_url(self):
        return f"{reverse('core:settings')}?tab=treasurer"

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        messages.success(self.request, f'Category "{form.instance.name}" created.')
        return super().form_valid(form)


class DeleteCategoryView(TreasurerRequiredMixin, MeetingMixin, DeleteView):
    """Delete expense category."""
    template_name = 'treasurer/category_confirm_delete.html'
    context_object_name = 'category'

    def get_success_url(self):
        return f"{reverse('core:settings')}?tab=treasurer"

    def get_queryset(self):
        return ExpenseCategory.objects.filter(meeting=self.get_meeting())


# ============================================================================
# Income Categories
# ============================================================================

class AddIncomeCategoryView(TreasurerRequiredMixin, MeetingMixin, CreateView):
    """Add income category."""
    template_name = 'treasurer/income_category_form.html'
    form_class = IncomeCategoryForm

    def get_success_url(self):
        return f"{reverse('core:settings')}?tab=treasurer"

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        messages.success(self.request, f'Income category "{form.instance.name}" created.')
        return super().form_valid(form)


class DeleteIncomeCategoryView(TreasurerRequiredMixin, MeetingMixin, DeleteView):
    """Delete income category."""
    template_name = 'treasurer/income_category_confirm_delete.html'
    context_object_name = 'category'

    def get_success_url(self):
        return f"{reverse('core:settings')}?tab=treasurer"

    def get_queryset(self):
        return IncomeCategory.objects.filter(meeting=self.get_meeting())


class SplitListView(LoginRequiredMixin, MeetingMixin, ListView):
    """List disbursement splits."""
    template_name = 'treasurer/split_list.html'
    context_object_name = 'splits'

    def get_queryset(self):
        return DisbursementSplit.objects.filter(
            meeting=self.get_meeting()
        ).prefetch_related('items')


class AddSplitView(TreasurerRequiredMixin, MeetingMixin, TemplateView):
    """Add disbursement split with inline items."""
    template_name = 'treasurer/split_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import DisbursementSplitItemFormSet
        if self.request.POST:
            context['form'] = DisbursementSplitForm(self.request.POST)
            context['formset'] = DisbursementSplitItemFormSet(self.request.POST)
        else:
            context['form'] = DisbursementSplitForm()
            context['formset'] = DisbursementSplitItemFormSet()
        return context

    def post(self, request, *args, **kwargs):
        from .forms import DisbursementSplitItemFormSet
        form = DisbursementSplitForm(request.POST)
        formset = DisbursementSplitItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            split = form.save(commit=False)
            split.meeting = self.get_meeting()
            split.save()

            formset.instance = split
            formset.save()

            messages.success(request, f'Split "{split.name}" created.')
            return redirect(f"{reverse('core:settings')}?tab=treasurer")

        return self.render_to_response(self.get_context_data())


class EditSplitView(TreasurerRequiredMixin, MeetingMixin, TemplateView):
    """Edit disbursement split with inline items."""
    template_name = 'treasurer/split_form.html'

    def get_split(self):
        return get_object_or_404(
            DisbursementSplit, pk=self.kwargs['pk'], meeting=self.get_meeting()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import DisbursementSplitItemFormSet
        split = self.get_split()
        context['split'] = split
        context['editing'] = True
        if self.request.POST:
            context['form'] = DisbursementSplitForm(self.request.POST, instance=split)
            context['formset'] = DisbursementSplitItemFormSet(self.request.POST, instance=split)
        else:
            context['form'] = DisbursementSplitForm(instance=split)
            context['formset'] = DisbursementSplitItemFormSet(instance=split)
        return context

    def post(self, request, *args, **kwargs):
        from .forms import DisbursementSplitItemFormSet
        split = self.get_split()
        form = DisbursementSplitForm(request.POST, instance=split)
        formset = DisbursementSplitItemFormSet(request.POST, instance=split)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Split "{split.name}" updated.')
            return redirect(f"{reverse('core:settings')}?tab=treasurer")

        return self.render_to_response(self.get_context_data())


class SetDefaultSplitView(TreasurerRequiredMixin, MeetingMixin, View):
    """Set a split as default."""

    def post(self, request, pk):
        split = get_object_or_404(
            DisbursementSplit, pk=pk, meeting=self.get_meeting()
        )
        split.is_default = True
        split.save()
        messages.success(request, f'"{split.name}" set as default.')
        return redirect(f"{reverse('core:settings')}?tab=treasurer")


class DeleteSplitView(TreasurerRequiredMixin, MeetingMixin, DeleteView):
    """Delete disbursement split."""
    template_name = 'treasurer/split_confirm_delete.html'
    context_object_name = 'split'

    def get_success_url(self):
        return f"{reverse('core:settings')}?tab=treasurer"

    def get_queryset(self):
        return DisbursementSplit.objects.filter(meeting=self.get_meeting())


# ============================================================================
# Recurring Expenses
# ============================================================================

class RecurringExpenseListView(LoginRequiredMixin, MeetingMixin, ListView):
    """List recurring expenses."""
    template_name = 'treasurer/recurring_list.html'
    context_object_name = 'recurring_expenses'

    def get_queryset(self):
        return RecurringExpense.objects.filter(meeting=self.get_meeting())


class AddRecurringExpenseView(TreasurerRequiredMixin, MeetingMixin, CreateView):
    """Add recurring expense."""
    template_name = 'treasurer/recurring_form.html'
    form_class = RecurringExpenseForm
    success_url = reverse_lazy('treasurer:recurring_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['meeting'] = self.get_meeting()
        return kwargs

    def form_valid(self, form):
        form.instance.meeting = self.get_meeting()
        messages.success(self.request, 'Recurring expense created.')
        return super().form_valid(form)


class DeleteRecurringExpenseView(TreasurerRequiredMixin, MeetingMixin, DeleteView):
    """Delete recurring expense."""
    template_name = 'treasurer/recurring_confirm_delete.html'
    success_url = reverse_lazy('treasurer:recurring_list')
    context_object_name = 'recurring_expense'

    def get_queryset(self):
        return RecurringExpense.objects.filter(meeting=self.get_meeting())


# ============================================================================
# HTMX Endpoints
# ============================================================================

class PreviewReportView(LoginRequiredMixin, MeetingMixin, View):
    """HTMX endpoint to preview report totals."""

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            return HttpResponse('')

        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            return HttpResponse('<p class="text-danger">Invalid date format</p>')

        service = self.get_service()
        totals = service.get_period_totals(start, end)

        html = f'''
        <div class="card">
            <div class="card-body">
                <h6>Preview</h6>
                <p>Income: <strong>${totals['total_income']}</strong></p>
                <p>Expenses: <strong>${totals['total_expenses']}</strong></p>
                <p>Net: <strong>${totals['net_amount']}</strong></p>
            </div>
        </div>
        '''
        return HttpResponse(html)


class CalculateSplitView(LoginRequiredMixin, MeetingMixin, View):
    """HTMX endpoint to calculate disbursement split."""

    def get(self, request):
        split_id = request.GET.get('split_id')
        amount = request.GET.get('amount')

        if not split_id or not amount:
            return HttpResponse('')

        try:
            split = DisbursementSplit.objects.get(
                pk=split_id, meeting=self.get_meeting()
            )
            amount = Decimal(amount)
        except (DisbursementSplit.DoesNotExist, ValueError):
            return HttpResponse('')

        splits = split.calculate_splits(amount)

        rows = ''.join([
            f'<tr><td>{s["name"]}</td><td>{s["percentage"]}%</td><td>${s["amount"]}</td></tr>'
            for s in splits
        ])

        html = f'''
        <table class="table table-sm">
            <thead><tr><th>Recipient</th><th>%</th><th>Amount</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        '''
        return HttpResponse(html)
