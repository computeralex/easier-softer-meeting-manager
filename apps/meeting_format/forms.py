"""
Meeting Format forms.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, HTML, Div

from .models import FormatBlock, BlockVariation, VariationSchedule, FormatModuleConfig, MeetingType


class FormatBlockForm(forms.ModelForm):
    """Form for creating/editing format blocks."""

    class Meta:
        model = FormatBlock
        fields = ['title', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', autofocus=True),
            Field('is_active'),
            Div(
                Submit('submit', 'Save Block', css_class='btn-primary'),
                HTML('<a href="{% url \'meeting_format:block_list\' %}" class="btn btn-outline-secondary ms-2">Cancel</a>'),
                css_class='mt-3'
            )
        )


class MeetingTypeForm(forms.ModelForm):
    """Form for creating/editing meeting types."""

    class Meta:
        model = MeetingType
        fields = ['name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', autofocus=True),
            Field('is_active'),
            Div(
                Submit('submit', 'Save Meeting Type', css_class='btn-primary'),
                HTML('<a href="{% url \'meeting_format:meeting_type_list\' %}" class="btn btn-outline-secondary ms-2">Cancel</a>'),
                css_class='mt-3'
            )
        )


class BlockVariationForm(forms.ModelForm):
    """Form for creating/editing block variations."""

    # Allow creating new meeting type inline
    new_meeting_type = forms.CharField(
        max_length=50,
        required=False,
        label='Or create new type',
        help_text='Leave empty to use selection above'
    )

    class Meta:
        model = BlockVariation
        fields = ['meeting_type', 'content', 'is_default', 'is_active']
        widgets = {
            'content': forms.HiddenInput(),  # Quill will populate this
        }

    def __init__(self, *args, **kwargs):
        self.meeting = kwargs.pop('meeting', None)
        super().__init__(*args, **kwargs)

        # Filter meeting_type queryset to this meeting
        if self.meeting:
            self.fields['meeting_type'].queryset = MeetingType.objects.filter(
                meeting=self.meeting,
                is_active=True
            )

        self.fields['meeting_type'].required = False
        self.fields['meeting_type'].empty_label = '(Default - no specific type)'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'variation-form'
        self.helper.layout = Layout(
            Field('meeting_type'),
            Field('new_meeting_type'),
            # Content field is hidden, Quill editor will be shown instead
            Field('content'),
            Field('is_default'),
            Field('is_active'),
            Div(
                Submit('submit', 'Save Content', css_class='btn-primary'),
                HTML('<a href="{% url \'meeting_format:block_list\' %}" class="btn btn-outline-secondary ms-2">Cancel</a>'),
                css_class='mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        meeting_type = cleaned_data.get('meeting_type')
        new_meeting_type = cleaned_data.get('new_meeting_type', '').strip()

        # If new type name provided, create it
        if new_meeting_type and self.meeting:
            meeting_type, created = MeetingType.objects.get_or_create(
                meeting=self.meeting,
                name=new_meeting_type,
                defaults={'is_active': True}
            )
            cleaned_data['meeting_type'] = meeting_type

        return cleaned_data


class VariationScheduleForm(forms.ModelForm):
    """Form for creating schedule rules."""

    class Meta:
        model = VariationSchedule
        fields = ['schedule_type', 'occurrence', 'weekday', 'specific_date']
        widgets = {
            'specific_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('schedule_type'),
            Div(
                Field('occurrence'),
                Field('weekday'),
                css_class='weekday-fields'
            ),
            Div(
                Field('specific_date'),
                css_class='date-field'
            ),
            Div(
                Submit('submit', 'Add Schedule', css_class='btn-primary'),
                HTML('<button type="button" class="btn btn-outline-secondary ms-2" data-bs-dismiss="modal">Cancel</button>'),
                css_class='mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get('schedule_type')

        if schedule_type == 'weekday_occurrence':
            if not cleaned_data.get('occurrence'):
                self.add_error('occurrence', 'Required for this schedule type')
            if cleaned_data.get('weekday') is None:
                self.add_error('weekday', 'Required for this schedule type')
        elif schedule_type == 'day_of_week':
            if cleaned_data.get('weekday') is None:
                self.add_error('weekday', 'Required for this schedule type')
        elif schedule_type == 'specific_date':
            if not cleaned_data.get('specific_date'):
                self.add_error('specific_date', 'Required for this schedule type')

        return cleaned_data


class FormatModuleConfigForm(forms.ModelForm):
    """Form for module configuration in settings."""

    class Meta:
        model = FormatModuleConfig
        fields = ['public_enabled']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('public_enabled'),
            Div(
                Submit('submit', 'Save Settings', css_class='btn-primary'),
                css_class='mt-3'
            )
        )
