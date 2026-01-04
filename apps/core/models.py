"""
Core models: User, ServicePosition, MeetingConfig, PositionAssignment.
"""
import re
import secrets
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class ServicePosition(models.Model):
    """
    Service positions that users can hold.
    e.g., treasurer, secretary, literature, gsr
    """
    # Basic info
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    # Configuration
    is_active = models.BooleanField(default=True)
    term_months = models.PositiveIntegerField(
        default=6,
        help_text='Default term length in months'
    )
    sobriety_requirement = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g., "1 year continuous"'
    )
    duties = models.TextField(blank=True, help_text='Position duties and responsibilities')
    sop = models.TextField(blank=True, help_text='Standard Operating Procedures')

    # Permissions
    can_manage_users = models.BooleanField(
        default=False,
        help_text='Can this position add/edit/remove users?'
    )
    module_permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text='Module access: {"treasurer": "write", "phone_list": "read"}'
    )

    # Display settings
    show_on_public_site = models.BooleanField(
        default=False,
        help_text='Show this position in the public officers directory'
    )
    warn_on_multiple_holders = models.BooleanField(
        default=True,
        help_text='Show warning when multiple people hold this position'
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['display_name']

    def __str__(self):
        return self.display_name

    @classmethod
    def generate_unique_slug(cls, display_name, exclude_pk=None):
        """
        Generate a unique slug from display_name.
        "Literature Chair" -> "literature_chair"
        If slug exists, appends numbers: literature_chair_2, literature_chair_3, etc.
        """
        # Convert to lowercase, replace non-alphanumeric with underscore
        slug = re.sub(r'[^a-z0-9]+', '_', display_name.lower()).strip('_')

        # Check if slug exists (excluding current instance if editing)
        queryset = cls.objects.filter(name=slug)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)

        if not queryset.exists():
            return slug

        # Append numbers until unique
        i = 2
        while True:
            new_slug = f"{slug}_{i}"
            queryset = cls.objects.filter(name=new_slug)
            if exclude_pk:
                queryset = queryset.exclude(pk=exclude_pk)
            if not queryset.exists():
                return new_slug
            i += 1

    def get_current_holders(self):
        """Get all current assignment records for this position."""
        return self.assignments.filter(end_date__isnull=True).select_related('user')

    def get_primary_holders(self):
        """Get current assignments where this is the user's primary position."""
        return self.assignments.filter(
            end_date__isnull=True,
            is_primary=True
        ).select_related('user')

    def get_secondary_holders(self):
        """Get current assignments where this is NOT the user's primary position."""
        return self.assignments.filter(
            end_date__isnull=True,
            is_primary=False
        ).select_related('user')

    def get_holder_count(self):
        """Get count of current holders (all)."""
        return self.assignments.filter(end_date__isnull=True).count()

    def get_primary_holder_count(self):
        """Get count of primary holders - these count as 'filled'."""
        return self.assignments.filter(end_date__isnull=True, is_primary=True).count()

    def is_vacant(self):
        """Check if position has no PRIMARY holders (still needs someone)."""
        return self.get_primary_holder_count() == 0

    def is_available(self):
        """
        Check if position is available (needs a primary holder).
        A position is available if it has no primary holder,
        even if someone is covering it as a secondary responsibility.
        """
        return self.get_primary_holder_count() == 0

    def has_multiple_holders(self):
        """Check if multiple people hold this position (all types)."""
        return self.get_holder_count() > 1

    def has_multiple_primary_holders(self):
        """Check if multiple people claim this as primary - may indicate an issue."""
        return self.get_primary_holder_count() > 1


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email authentication and multiple service positions.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=255, blank=True)  # Legacy field, use first_name/last_name
    # Legacy M2M - being replaced by PositionAssignment for term tracking
    # Keep for backwards compatibility during migration
    positions = models.ManyToManyField(
        ServicePosition,
        blank=True,
        related_name='users',
        help_text='[DEPRECATED] Use PositionAssignment instead'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        """Return the user's full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.name

    def get_short_name(self):
        """Return first name and last initial."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name[0]}."
        return self.first_name or self.get_full_name()

    # -------------------------------------------------------------------------
    # Position checking methods (use PositionAssignment)
    # -------------------------------------------------------------------------

    @property
    def current_positions(self):
        """Get ServicePositions currently held by this user."""
        return ServicePosition.objects.filter(
            assignments__user=self,
            assignments__end_date__isnull=True
        ).distinct()

    @property
    def current_assignments(self):
        """Get current PositionAssignment records for this user."""
        return self.position_assignments.filter(end_date__isnull=True).select_related('position')

    @property
    def primary_assignment(self):
        """Get the user's primary position assignment (if any)."""
        return self.position_assignments.filter(
            end_date__isnull=True,
            is_primary=True
        ).select_related('position').first()

    @property
    def primary_position(self):
        """Get the user's primary position (if any)."""
        assignment = self.primary_assignment
        return assignment.position if assignment else None

    @property
    def secondary_assignments(self):
        """Get the user's secondary position assignments."""
        return self.position_assignments.filter(
            end_date__isnull=True,
            is_primary=False
        ).select_related('position')

    def has_position(self, position_name: str) -> bool:
        """Check if user currently holds a specific position."""
        # Check PositionAssignment first (new system)
        if self.position_assignments.filter(
            position__name=position_name,
            end_date__isnull=True
        ).exists():
            return True
        # Fallback to legacy M2M during migration
        return self.positions.filter(name=position_name).exists()

    def has_any_position(self, position_names: list) -> bool:
        """Check if user currently holds any of the specified positions."""
        # Check PositionAssignment first (new system)
        if self.position_assignments.filter(
            position__name__in=position_names,
            end_date__isnull=True
        ).exists():
            return True
        # Fallback to legacy M2M during migration
        return self.positions.filter(name__in=position_names).exists()

    @property
    def position_names(self) -> list:
        """Get list of position names currently held by this user."""
        # Get from PositionAssignment
        assignment_names = list(
            self.position_assignments.filter(end_date__isnull=True)
            .values_list('position__name', flat=True)
        )
        if assignment_names:
            return assignment_names
        # Fallback to legacy M2M
        return list(self.positions.values_list('name', flat=True))

    @property
    def is_service_position_holder(self) -> bool:
        """Check if user currently holds any service position."""
        if self.position_assignments.filter(end_date__isnull=True).exists():
            return True
        return self.positions.exists()

    # -------------------------------------------------------------------------
    # Module permission methods
    # -------------------------------------------------------------------------

    def has_module_permission(self, module_name: str, level: str = 'read') -> bool:
        """
        Check if user has permission for a module via any current position.
        Level can be 'read' or 'write'. Write implies read.
        """
        if self.is_superuser:
            return True

        for assignment in self.current_assignments:
            perms = assignment.position.module_permissions.get(module_name)
            if perms == 'write':
                return True
            if perms == 'read' and level == 'read':
                return True
        return False

    def can_manage_users(self) -> bool:
        """Check if user can manage other users via any current position."""
        if self.is_superuser:
            return True
        return self.current_assignments.filter(position__can_manage_users=True).exists()

    def get_module_permissions(self) -> dict:
        """Get combined module permissions from all current positions."""
        permissions = {}
        for assignment in self.current_assignments:
            for module, level in assignment.position.module_permissions.items():
                # Write overrides read
                if level == 'write' or permissions.get(module) != 'write':
                    permissions[module] = level
        return permissions


class MeetingConfig(models.Model):
    """
    Global meeting configuration.
    Singleton pattern - only one record exists.
    """
    SOBRIETY_TERM_CHOICES = [
        ('sobriety', 'Sobriety'),
        ('abstinence', 'Abstinence'),
        ('clean', 'Clean Time'),
        ('recovery', 'Recovery'),
        ('other', 'Other'),
    ]

    PUBLIC_OFFICERS_DISPLAY_CHOICES = [
        ('hidden', 'Not visible'),
        ('positions_only', 'Positions and vacancy status only'),
        ('names', 'Positions, vacancy, and officer first name + last initial'),
    ]

    meeting_name = models.CharField(max_length=255, default='My Meeting')
    meeting_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g., Open, Closed, Speaker, Step Study'
    )
    meeting_day = models.CharField(max_length=20, blank=True)
    meeting_time = models.TimeField(null=True, blank=True)
    meeting_timezone = models.CharField(max_length=50, default='America/Los_Angeles')
    meeting_address = models.TextField(blank=True)
    zoom_id = models.CharField(max_length=50, blank=True)
    zoom_password = models.CharField(max_length=50, blank=True)
    group_service_number = models.CharField(max_length=50, blank=True)
    share_token = models.CharField(max_length=128, unique=True, blank=True)
    sobriety_term = models.CharField(
        max_length=20,
        choices=SOBRIETY_TERM_CHOICES,
        default='sobriety',
    )
    sobriety_term_other = models.CharField(
        max_length=50,
        blank=True,
        help_text='Custom term if "Other" is selected'
    )
    public_officers_display = models.CharField(
        max_length=20,
        choices=PUBLIC_OFFICERS_DISPLAY_CHOICES,
        default='positions_only',
        help_text='How to display service positions on the public site'
    )

    class Meta:
        verbose_name = 'Meeting Configuration'
        verbose_name_plural = 'Meeting Configuration'

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        # Generate share token if not set
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.meeting_name

    def regenerate_share_token(self):
        """Generate a new share token."""
        self.share_token = secrets.token_urlsafe(32)
        self.save(update_fields=['share_token'])

    def get_sobriety_term_label(self):
        """Get the sobriety term label for display."""
        if self.sobriety_term == 'other' and self.sobriety_term_other:
            return self.sobriety_term_other
        return self.get_sobriety_term_display()


class PositionAssignment(models.Model):
    """
    Tracks who holds service positions, with start/end dates for history.
    Replaces the simple User.positions M2M to enable term tracking.

    Primary vs Secondary:
    - Each user with multiple positions has exactly ONE primary position
    - Primary positions are considered "taken" (the position is filled)
    - Secondary positions are considered "available" (the person is helping but
      the position still needs a dedicated holder)
    """
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='position_assignments'
    )
    position = models.ForeignKey(
        ServicePosition,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    is_primary = models.BooleanField(
        default=True,
        help_text='Primary position = filled. Secondary = position still needs someone.'
    )
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Leave blank for current holders'
    )
    notes = models.TextField(
        blank=True,
        help_text='e.g., "Appointed mid-term to replace previous holder"'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']
        verbose_name = 'Position Assignment'
        verbose_name_plural = 'Position Assignments'

    def __str__(self):
        status = 'current' if self.is_current else f'ended {self.end_date}'
        return f"{self.user} - {self.position} ({status})"

    @property
    def is_current(self):
        """Check if this is a current (active) assignment."""
        return self.end_date is None

    @property
    def expected_end_date(self):
        """Calculate expected end date based on position term length."""
        if self.end_date:
            return self.end_date
        return self.start_date + relativedelta(months=self.position.term_months)

    @property
    def is_term_ending_soon(self):
        """Check if term ends within 30 days."""
        if not self.is_current:
            return False
        expected_end = self.expected_end_date
        return expected_end <= date.today() + timedelta(days=30)

    @property
    def is_term_overdue(self):
        """Check if term has passed its expected end date."""
        if not self.is_current:
            return False
        return self.expected_end_date < date.today()

    @property
    def days_until_term_end(self):
        """Get days until expected term end (negative if overdue)."""
        if not self.is_current:
            return None
        return (self.expected_end_date - date.today()).days

    def end_term(self, end_date=None):
        """End this assignment."""
        self.end_date = end_date or date.today()
        self.save(update_fields=['end_date', 'updated_at'])
