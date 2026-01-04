"""
Readings forms.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div

from .models import Reading, ReadingCategory


class ReadingForm(forms.ModelForm):
    """Form for creating/editing readings."""

    class Meta:
        model = Reading
        fields = ['title', 'short_name', 'content', 'category', 'notes', 'copyright_notice', 'is_active', 'noindex']
        widgets = {
            'content': forms.Textarea(attrs={
                'id': 'reading-content',
                'class': 'quill-editor-input',
                'style': 'display: none;'  # Hidden, Quill will handle display
            }),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting

        # Filter categories to this meeting only
        if meeting:
            self.fields['category'].queryset = ReadingCategory.objects.filter(
                meeting=meeting,
                is_active=True
            )

        self.fields['category'].required = False
        self.fields['category'].empty_label = '(No category)'
        self.fields['notes'].required = False

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'short_name',
            'category',
            # Quill editor container - the actual editor
            HTML('''
                <div class="mb-3">
                    <label class="form-label">Content</label>
                    <div id="quill-editor" class="quill-container"></div>
                </div>
            '''),
            Field('content', type='hidden'),  # Hidden field to store HTML
            'notes',
            'is_active',
            Submit('submit', 'Save Reading', css_class='btn-primary mt-3')
        )


class ReadingCategoryForm(forms.ModelForm):
    """Form for creating/editing reading categories."""

    class Meta:
        model = ReadingCategory
        fields = ['name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'is_active',
            Submit('submit', 'Save Category', css_class='btn-primary mt-3')
        )


class ImportReadingForm(forms.Form):
    """Form for importing readings from text."""
    title = forms.CharField(
        max_length=200,
        help_text='Title for this reading'
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10}),
        help_text='Paste the reading text here'
    )
    category = forms.ModelChoiceField(
        queryset=ReadingCategory.objects.none(),
        required=False,
        empty_label='(No category)'
    )

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meeting:
            self.fields['category'].queryset = ReadingCategory.objects.filter(
                meeting=meeting,
                is_active=True
            )

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'content',
            'category',
            Submit('submit', 'Import Reading', css_class='btn-primary mt-3')
        )
