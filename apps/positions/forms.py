"""
Forms for service position management.
"""
from datetime import date

from django import forms

from apps.core.models import ServicePosition, PositionAssignment, User


class ServicePositionForm(forms.ModelForm):
    """Form for creating/editing service positions."""

    class Meta:
        model = ServicePosition
        fields = [
            'display_name',
            'description',
            'term_months',
            'sobriety_requirement',
            'duties',
            'sop',
            'can_manage_users',
            'warn_on_multiple_holders',
            'is_active',
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'term_months': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 36}),
            'sobriety_requirement': forms.TextInput(attrs={'class': 'form-control'}),
            'duties': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'sop': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'display_name': 'Name',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-generate slug from display_name for new positions
        if not instance.pk:
            instance.name = ServicePosition.generate_unique_slug(instance.display_name)
        if commit:
            instance.save()
        return instance


class ModulePermissionsForm(forms.Form):
    """Form for editing a position's module permissions."""

    PERMISSION_CHOICES = [
        ('none', 'No Access'),
        ('read', 'Read Only'),
        ('write', 'Read & Write'),
    ]

    def __init__(self, *args, position=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.position = position

        # Get available modules
        from apps.registry.module_registry import registry
        modules = registry.get_all_modules()

        current_perms = position.module_permissions if position else {}

        for name, module in modules.items():
            config = module.config
            field_name = f'module_{config.name}'
            current_value = current_perms.get(config.name, 'none')

            self.fields[field_name] = forms.ChoiceField(
                label=config.verbose_name,
                choices=self.PERMISSION_CHOICES,
                initial=current_value,
                widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
                required=False,
            )

    def save(self):
        """Save the module permissions to the position."""
        if not self.position:
            return

        permissions = {}
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('module_') and value != 'none':
                module_name = field_name[7:]  # Remove 'module_' prefix
                permissions[module_name] = value

        self.position.module_permissions = permissions
        self.position.save(update_fields=['module_permissions', 'updated_at'])


class PositionAssignmentForm(forms.ModelForm):
    """Form for assigning a user to a position."""

    class Meta:
        model = PositionAssignment
        fields = ['user', 'is_primary', 'start_date', 'end_date', 'notes']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'is_primary': 'Primary position',
        }
        help_texts = {
            'is_primary': 'If checked, this position is considered "filled" by this person. '
                          'If unchecked, this is a secondary responsibility and the position '
                          'is still considered available.',
        }

    def __init__(self, *args, position=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.position = position

        # Only show active users
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')

        # Set default start date to today
        if not self.instance.pk:
            self.fields['start_date'].initial = date.today()

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        is_primary = cleaned_data.get('is_primary')

        # If setting as primary, check if user already has another primary
        if user and is_primary:
            existing_primary = PositionAssignment.objects.filter(
                user=user,
                is_primary=True,
                end_date__isnull=True
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_primary.exists():
                existing = existing_primary.first()
                raise forms.ValidationError(
                    f'{user} already has a primary position ({existing.position.display_name}). '
                    f'Either make this a secondary position, or change their other position first.'
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.position:
            instance.position = self.position
        if commit:
            instance.save()
        return instance


class EndTermForm(forms.Form):
    """Form for ending a position assignment."""

    end_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
