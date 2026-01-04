"""
Treasurer forms.
"""
from datetime import date
from decimal import Decimal
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML

from apps.core.validators import validate_receipt_file
from .models import (
    TreasurerSettings, TreasurerRecord, ExpenseCategory, IncomeCategory,
    DisbursementSplit, DisbursementSplitItem, RecurringExpense
)


class SetupForm(forms.ModelForm):
    """Initial treasurer setup form."""

    class Meta:
        model = TreasurerSettings
        fields = ['starting_balance', 'prudent_reserve']
        widgets = {
            'starting_balance': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'prudent_reserve': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'starting_balance',
            'prudent_reserve',
            Submit('submit', 'Save Settings', css_class='btn-primary mt-3')
        )


class TreasurerSettingsForm(forms.ModelForm):
    """Treasurer settings form."""

    class Meta:
        model = TreasurerSettings
        fields = ['starting_balance', 'prudent_reserve']
        widgets = {
            'starting_balance': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'prudent_reserve': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
        help_texts = {
            'starting_balance': 'The amount in your treasury when you started tracking. This is separate from the prudent reserve.',
            'prudent_reserve': 'Amount to keep in reserve (not available for disbursement). Available funds = Current Balance - Prudent Reserve.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['starting_balance'].label = 'Starting Balance'
        self.fields['prudent_reserve'].label = 'Prudent Reserve'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'starting_balance',
            'prudent_reserve',
            Submit('submit', 'Save Settings', css_class='btn-primary mt-3')
        )


class AddRecordForm(forms.Form):
    """Form for adding income or expense."""
    RECORD_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    record_type = forms.ChoiceField(
        choices=RECORD_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='income'
    )
    date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'})
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        help_text='Optional description'
    )
    income_category = forms.ModelChoiceField(
        queryset=IncomeCategory.objects.none(),
        required=False,
        help_text='Category for income'
    )
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.none(),
        required=False,
        help_text='Category for expenses'
    )
    disbursement_split = forms.ModelChoiceField(
        queryset=DisbursementSplit.objects.none(),
        required=False,
        help_text='Optional: split this expense among recipients'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )
    receipt = forms.FileField(
        required=False,
        help_text='Upload receipt image (JPG, PNG) or PDF'
    )

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meeting:
            self.fields['income_category'].queryset = IncomeCategory.objects.filter(
                meeting=meeting, is_active=True
            )
            # Set default income category
            default_income = IncomeCategory.objects.filter(
                meeting=meeting, is_default=True
            ).first()
            if default_income:
                self.fields['income_category'].initial = default_income

            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                meeting=meeting, is_active=True
            )
            self.fields['disbursement_split'].queryset = DisbursementSplit.objects.filter(
                meeting=meeting
            )

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            'record_type',
            Row(
                Column('date', css_class='col-md-6'),
                Column('amount', css_class='col-md-6'),
            ),
            'description',
            'income_category',
            'category',
            'disbursement_split',
            Div(id='split-preview'),  # HTMX will populate this
            'notes',
            'receipt',
            Submit('submit', 'Add Transaction', css_class='btn-primary mt-3')
        )

    def clean_receipt(self):
        """Validate receipt file type using magic bytes."""
        receipt = self.cleaned_data.get('receipt')
        if receipt:
            validate_receipt_file(receipt)
        return receipt

    def clean(self):
        cleaned_data = super().clean()
        record_type = cleaned_data.get('record_type')
        description = cleaned_data.get('description')

        if record_type == 'expense':
            if not description:
                self.add_error('description', 'Description is required for expenses.')

        return cleaned_data


class EditRecordForm(forms.ModelForm):
    """Form for editing an existing transaction."""

    class Meta:
        model = TreasurerRecord
        fields = ['date', 'amount', 'description', 'income_category', 'category', 'notes', 'receipt']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meeting:
            self.fields['income_category'].queryset = IncomeCategory.objects.filter(
                meeting=meeting, is_active=True
            )
            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                meeting=meeting, is_active=True
            )

        # Hide irrelevant category field based on record type
        instance = kwargs.get('instance')
        if instance:
            if instance.type == TreasurerRecord.RecordType.INCOME:
                del self.fields['category']
            else:
                del self.fields['income_category']

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Row(
                Column('date', css_class='col-md-6'),
                Column('amount', css_class='col-md-6'),
            ),
            'description',
            'income_category' if instance and instance.type == TreasurerRecord.RecordType.INCOME else 'category',
            'notes',
            'receipt',
            Submit('submit', 'Save Changes', css_class='btn-primary mt-3')
        )

    def clean_receipt(self):
        """Validate receipt file type using magic bytes."""
        receipt = self.cleaned_data.get('receipt')
        if receipt:
            validate_receipt_file(receipt)
        return receipt


class CreateReportForm(forms.Form):
    """Form for creating a report."""
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, meeting=None, **kwargs):
        self.meeting = meeting
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('start_date', css_class='col-md-6'),
                Column('end_date', css_class='col-md-6'),
            ),
            Div(id='report-preview'),  # HTMX will populate this
            Submit('submit', 'Create Report', css_class='btn-primary mt-3')
        )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        if start and end:
            if start > end:
                self.add_error('end_date', 'End date must be after start date.')

            if end > date.today():
                self.add_error('end_date', 'End date cannot be in the future.')

        return cleaned_data


class IncomeCategoryForm(forms.ModelForm):
    """Form for income category."""

    class Meta:
        model = IncomeCategory
        fields = ['name', 'is_default']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'is_default',
            Submit('submit', 'Save Category', css_class='btn-primary mt-3')
        )


class CategoryForm(forms.ModelForm):
    """Form for expense category."""

    class Meta:
        model = ExpenseCategory
        fields = ['name', 'is_disbursement']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'is_disbursement',
            Submit('submit', 'Save Category', css_class='btn-primary mt-3')
        )


class DisbursementSplitForm(forms.ModelForm):
    """Form for disbursement split configuration."""

    class Meta:
        model = DisbursementSplit
        fields = ['name', 'is_default']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False  # We'll handle form tag in template


class DisbursementSplitItemForm(forms.ModelForm):
    """Form for individual split item."""

    class Meta:
        model = DisbursementSplitItem
        fields = ['name', 'percentage']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., District, Area'}),
            'percentage': forms.NumberInput(attrs={'placeholder': '%', 'min': '0', 'max': '100', 'step': '0.01'}),
        }


# Inline formset for split items
DisbursementSplitItemFormSet = forms.inlineformset_factory(
    DisbursementSplit,
    DisbursementSplitItem,
    form=DisbursementSplitItemForm,
    fields=['name', 'percentage'],
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class RecurringExpenseForm(forms.ModelForm):
    """Form for recurring expense."""

    class Meta:
        model = RecurringExpense
        fields = ['description', 'amount', 'category', 'frequency', 'next_due_date', 'notes']
        widgets = {
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meeting:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                meeting=meeting, is_active=True
            )

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'description',
            Row(
                Column('amount', css_class='col-md-6'),
                Column('frequency', css_class='col-md-6'),
            ),
            'category',
            'next_due_date',
            'notes',
            Submit('submit', 'Save', css_class='btn-primary mt-3')
        )
