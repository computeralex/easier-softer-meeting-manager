"""
Core forms.
"""
from datetime import date

from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div

from .models import MeetingConfig, User, ServicePosition, PositionAssignment


class SetupWizardForm(forms.ModelForm):
    """Form for initial setup wizard."""

    class Meta:
        model = MeetingConfig
        fields = ['meeting_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['meeting_name'].label = 'What is your group called?'
        self.fields['meeting_name'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g., Saturday Morning Group'
        })


class MeetingConfigForm(forms.ModelForm):
    """Form for editing global meeting settings."""

    class Meta:
        model = MeetingConfig
        fields = ['meeting_name', 'sobriety_term', 'sobriety_term_other', 'logo', 'favicon']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['meeting_name'].label = 'Group Name'
        self.fields['sobriety_term'].label = 'Recovery Term'
        self.fields['sobriety_term_other'].label = 'Custom Term'
        self.fields['sobriety_term_other'].help_text = ''
        self.fields['logo'].label = 'Logo'
        self.fields['logo'].help_text = 'Logo for website header (max 200px height recommended)'
        self.fields['favicon'].label = 'Favicon'
        self.fields['favicon'].help_text = 'Browser tab icon (32x32 or 64x64 PNG/ICO recommended)'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            'meeting_name',
            Row(
                Column('sobriety_term', css_class='col-md-6'),
                Column('sobriety_term_other', css_class='col-md-6'),
            ),
            Row(
                Column('logo', css_class='col-md-6'),
                Column('favicon', css_class='col-md-6'),
            ),
            Submit('submit', 'Save', css_class='btn-primary mt-3')
        )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email Address'
        self.fields['first_name'].label = 'First Name'
        self.fields['last_name'].label = 'Last Name'
        self.fields['phone'].label = 'Phone Number'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'email',
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            'phone',
            Submit('submit', 'Save', css_class='btn-primary mt-3')
        )


class UserForm(forms.ModelForm):
    """Form for admin creating/editing users with position assignment."""

    primary_position = forms.ModelChoiceField(
        queryset=ServicePosition.objects.filter(is_active=True),
        widget=forms.Select,
        required=True,
        label='Primary Service Position'
    )

    secondary_positions = forms.ModelMultipleChoiceField(
        queryset=ServicePosition.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Secondary Positions (temporary coverage)'
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'is_active', 'is_superuser']

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email Address'
        self.fields['email'].required = False
        self.fields['email'].help_text = 'Leave blank for placeholder users (cannot log in)'
        self.fields['first_name'].label = 'First Name'
        self.fields['first_name'].required = True  # Required for placeholders
        self.fields['last_name'].label = 'Last Name'
        self.fields['phone'].label = 'Phone Number'
        self.fields['is_active'].label = 'Account Active'
        self.fields['is_active'].help_text = 'Inactive users cannot log in'
        self.fields['is_superuser'].label = 'Administrator'
        self.fields['is_superuser'].help_text = 'Full access to all features and settings'

        # Only superusers can grant superuser status
        if not self.request_user or not self.request_user.is_superuser:
            del self.fields['is_superuser']

        # Get Group Member as default
        group_member = ServicePosition.objects.filter(name='group_member').first()

        # Set primary position queryset - exclude membership positions
        self.fields['primary_position'].queryset = ServicePosition.objects.filter(
            is_active=True,
            is_membership_position=False
        ).order_by('display_name')

        if not self.instance.pk and group_member:
            self.fields['primary_position'].initial = group_member

        # Secondary positions: exclude membership positions
        self.fields['secondary_positions'].queryset = ServicePosition.objects.filter(
            is_active=True,
            is_membership_position=False
        ).order_by('display_name')

        # Pre-populate from existing assignments if editing
        if self.instance.pk:
            primary = self.instance.primary_assignment
            if primary:
                self.fields['primary_position'].initial = primary.position

            self.fields['secondary_positions'].initial = [
                a.position for a in self.instance.secondary_assignments
            ]

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'email',
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            'phone',
            HTML('<hr class="my-3">'),
            'primary_position',
            HTML('<p class="text-muted small mb-3">The user\'s main service role. "Group Member" for regular members.</p>'),
            'secondary_positions',
            HTML('<p class="text-muted small mb-3">Additional positions this user is temporarily covering. These positions still show as "available" in the Service module.</p>'),
            HTML('<hr class="my-3">'),
            'is_active',
            Submit('submit', 'Save', css_class='btn-primary mt-3')
        )

    def clean_email(self):
        """Convert empty email to None for database uniqueness."""
        email = self.cleaned_data.get('email')
        if not email:
            return None
        # Check for duplicates (excluding current instance)
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        first_name = cleaned_data.get('first_name')

        # Placeholder users (no email) must have a first name
        if not email and not first_name:
            raise forms.ValidationError(
                'First name is required for placeholder users (users without email).'
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # End all current assignments
            user.position_assignments.filter(end_date__isnull=True).update(
                end_date=date.today()
            )

            # Create primary assignment
            primary = self.cleaned_data.get('primary_position')
            if primary:
                PositionAssignment.objects.create(
                    user=user,
                    position=primary,
                    is_primary=True
                )

            # Create secondary assignments
            for position in self.cleaned_data.get('secondary_positions', []):
                PositionAssignment.objects.create(
                    user=user,
                    position=position,
                    is_primary=False
                )
        return user


class UserInviteForm(forms.Form):
    """Form for inviting new users or creating placeholder users."""
    email = forms.EmailField(
        label='Email Address',
        required=False,
        help_text='Leave blank to create a placeholder user (cannot log in)'
    )
    first_name = forms.CharField(max_length=100, required=False, label='First Name')
    last_name = forms.CharField(max_length=100, required=False, label='Last Name')
    primary_position = forms.ModelChoiceField(
        queryset=ServicePosition.objects.filter(is_active=True),
        widget=forms.Select,
        required=True,
        label='Primary Service Position'
    )
    secondary_positions = forms.ModelMultipleChoiceField(
        queryset=ServicePosition.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Secondary Positions (temporary coverage)'
    )
    send_email = forms.BooleanField(
        initial=True,
        required=False,
        label='Send welcome email with login credentials'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get Group Member as default
        group_member = ServicePosition.objects.filter(name='group_member').first()
        if group_member:
            self.fields['primary_position'].initial = group_member

        # Exclude membership positions from dropdowns
        self.fields['primary_position'].queryset = ServicePosition.objects.filter(
            is_active=True,
            is_membership_position=False
        ).order_by('display_name')

        self.fields['secondary_positions'].queryset = ServicePosition.objects.filter(
            is_active=True,
            is_membership_position=False
        ).order_by('display_name')

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'email',
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            HTML('<hr class="my-3">'),
            'primary_position',
            'secondary_positions',
            HTML('<hr class="my-3">'),
            'send_email',
            Submit('submit', 'Invite User', css_class='btn-primary mt-3')
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return None
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        first_name = cleaned_data.get('first_name')

        # Placeholder users must have a first name
        if not email and not first_name:
            raise forms.ValidationError(
                'First name is required for placeholder users (users without email).'
            )
        return cleaned_data


class PasswordChangeFormStyled(DjangoPasswordChangeForm):
    """Django's PasswordChangeForm with crispy styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'old_password',
            'new_password1',
            'new_password2',
            Submit('submit', 'Change Password', css_class='btn-primary mt-3')
        )
