"""
Website forms.
"""
from django import forms
from django.utils.text import slugify
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

from .models import WebsitePage


class WebsitePageForm(forms.ModelForm):
    """Form for editing CMS page metadata (not content - that's in Puck editor)."""

    # Simple CharField for image path (not URLField since we store relative paths)
    featured_image = forms.CharField(required=False)

    class Meta:
        model = WebsitePage
        fields = ['title', 'slug', 'meta_title', 'meta_description', 'featured_image', 'is_published', 'show_in_nav', 'nav_order']
        widgets = {
            'nav_order': forms.NumberInput(attrs={'min': 0}),
            'meta_title': forms.TextInput(attrs={'maxlength': 70}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'maxlength': 160}),
        }

    def __init__(self, *args, **kwargs):
        self.meeting = kwargs.pop('meeting', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'slug',
            'is_published',
            'show_in_nav',
            'nav_order',
            Submit('submit', 'Save Settings', css_class='btn-primary mt-3')
        )

    def clean_slug(self):
        """Ensure slug is unique for this meeting."""
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Auto-generate from title
            slug = slugify(self.cleaned_data.get('title', ''))

        # Check uniqueness
        qs = WebsitePage.objects.filter(meeting=self.meeting, slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A page with this slug already exists.')

        return slug

    def save(self, commit=True):
        page = super().save(commit=False)
        if self.meeting:
            page.meeting = self.meeting
        if commit:
            page.save()
        return page
