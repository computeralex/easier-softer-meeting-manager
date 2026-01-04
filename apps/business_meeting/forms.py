"""
Business Meeting forms.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML

from .models import BusinessMeetingFormat, BusinessMeeting


class BusinessMeetingFormatForm(forms.ModelForm):
    """Form for editing the business meeting format template."""

    class Meta:
        model = BusinessMeetingFormat
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'id': 'format-content',
                'class': 'quill-editor-input',
                'style': 'display: none;'  # Hidden, Quill will handle display
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            # Quill editor container
            HTML('''
                <div class="mb-3">
                    <label class="form-label">Business Meeting Format</label>
                    <div id="quill-editor" class="quill-container"></div>
                </div>
            '''),
            Field('content', type='hidden'),
            Submit('submit', 'Save Format', css_class='btn-primary mt-3')
        )


class BusinessMeetingForm(forms.ModelForm):
    """Form for creating/editing business meeting notes."""

    class Meta:
        model = BusinessMeeting
        fields = ['date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'id': 'notes-content',
                'class': 'quill-editor-input',
                'style': 'display: none;'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'date',
            # Quill editor container
            HTML('''
                <div class="mb-3">
                    <label class="form-label">Notes</label>
                    <div id="quill-editor" class="quill-container"></div>
                </div>
            '''),
            Field('notes', type='hidden'),
            Submit('submit', 'Save Meeting', css_class='btn-primary mt-3')
        )
