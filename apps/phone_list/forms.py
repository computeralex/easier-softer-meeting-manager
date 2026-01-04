"""
Phone List forms.
"""
from django import forms
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML

from .models import Contact, TimeZone


class ContactForm(forms.ModelForm):
    """Form for creating/editing contacts."""

    class Meta:
        model = Contact
        fields = [
            'name', 'phone', 'has_whatsapp', 'email',
            'available_to_sponsor', 'sobriety_date', 'time_zone', 'time_zone_other', 'notes'
        ]
        widgets = {
            'sobriety_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    # Special value for "Other" option
    OTHER_TZ_VALUE = 'other'

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting

        # Build time zone choices manually to add "Other" option
        tz_qs = TimeZone.objects.filter(is_active=True)
        if meeting:
            tz_qs = tz_qs.filter(models.Q(meeting=meeting) | models.Q(meeting__isnull=True))

        tz_choices = [('', '(Not specified)')]
        tz_choices += [(str(tz.pk), tz.display_name) for tz in tz_qs]
        tz_choices.append((self.OTHER_TZ_VALUE, 'Other'))

        self.fields['time_zone'] = forms.ChoiceField(
            choices=tz_choices,
            required=False,
            label='Time Zone'
        )
        self.fields['time_zone_other'].label = 'Specify time zone'
        self.fields['time_zone_other'].required = False

        # If editing and has other value, select "Other"
        if self.instance and self.instance.pk:
            if self.instance.time_zone_other and not self.instance.time_zone:
                self.initial['time_zone'] = self.OTHER_TZ_VALUE
            elif self.instance.time_zone:
                self.initial['time_zone'] = str(self.instance.time_zone.pk)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            Row(
                Column('phone', css_class='col-md-6'),
                Column('has_whatsapp', css_class='col-md-6 d-flex align-items-center pt-4'),
            ),
            'email',
            'available_to_sponsor',
            'sobriety_date',
            Row(
                Column(Field('time_zone', css_id='id_time_zone'), css_class='col-md-6'),
                Column(Field('time_zone_other', wrapper_class='tz-other-wrapper'), css_class='col-md-6'),
            ),
            'notes',
            Submit('submit', 'Save', css_class='btn-primary mt-3')
        )

    def clean(self):
        cleaned_data = super().clean()
        tz_value = cleaned_data.get('time_zone')
        tz_other = cleaned_data.get('time_zone_other', '').strip()

        # Convert time_zone from string to actual object or None
        if tz_value == self.OTHER_TZ_VALUE:
            cleaned_data['time_zone'] = None
            # time_zone_other keeps its value
        elif tz_value:
            try:
                cleaned_data['time_zone'] = TimeZone.objects.get(pk=int(tz_value))
                cleaned_data['time_zone_other'] = ''  # Clear other if selecting a real TZ
            except (TimeZone.DoesNotExist, ValueError):
                cleaned_data['time_zone'] = None
        else:
            cleaned_data['time_zone'] = None
            cleaned_data['time_zone_other'] = ''  # Clear other if no selection

        return cleaned_data


class TimeZoneForm(forms.ModelForm):
    """Form for adding/editing time zones."""

    class Meta:
        model = TimeZone
        fields = ['code', 'display_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].label = 'Code'
        self.fields['display_name'].label = 'Display Name'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('code', css_class='col-md-4'),
                Column('display_name', css_class='col-md-8'),
            ),
            Submit('submit', 'Add Time Zone', css_class='btn-primary mt-3')
        )


class CSVUploadForm(forms.Form):
    """Form for uploading CSV file."""
    file = forms.FileField(
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            'file',
            Submit('submit', 'Upload', css_class='btn-primary mt-3')
        )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('Please upload a CSV file.')
        return file


class CSVMappingForm(forms.Form):
    """Dynamic form for mapping CSV columns to Contact fields."""

    IMPORT_MODES = [
        ('add', 'Add new contacts only'),
        ('update', 'Update existing contacts (match by name)'),
        ('replace', 'Replace all contacts (delete existing first)'),
    ]

    import_mode = forms.ChoiceField(
        choices=IMPORT_MODES,
        initial='add',
        widget=forms.RadioSelect
    )

    def __init__(self, headers, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Available Contact fields
        contact_fields = [
            ('', '-- Skip this column --'),
            ('name', 'Name'),
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('has_whatsapp', 'Has WhatsApp'),
            ('available_to_sponsor', 'Available to Sponsor'),
            ('sobriety_date', 'Sobriety Date'),
            ('time_zone', 'Time Zone'),
            ('notes', 'Notes'),
        ]

        # Create a field for each CSV header
        for header in headers:
            field_name = f'col_{header}'
            self.fields[field_name] = forms.ChoiceField(
                choices=contact_fields,
                required=False,
                label=header
            )

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<div class="mb-4"><h6>Import Mode</h6></div>'),
            'import_mode',
            HTML('<hr class="my-4"><div class="mb-3"><h6>Column Mapping</h6><p class="text-muted small">Map each CSV column to a contact field.</p></div>'),
            *[Field(f'col_{h}') for h in headers],
            Submit('submit', 'Preview Import', css_class='btn-primary mt-3')
        )

    def get_mapping(self):
        """Extract the field mapping from cleaned data."""
        mapping = {}
        for key, value in self.cleaned_data.items():
            if key.startswith('col_') and value:
                csv_header = key[4:]  # Remove 'col_' prefix
                mapping[value] = csv_header
        return mapping


class CSVConfirmForm(forms.Form):
    """Confirmation form for CSV import."""
    confirm = forms.BooleanField(
        required=True,
        label='I confirm the data above is correct'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'confirm',
            Submit('submit', 'Import Contacts', css_class='btn-primary mt-3')
        )
