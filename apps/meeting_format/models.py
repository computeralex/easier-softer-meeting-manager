"""
Meeting Format models.
"""
import secrets

from django.db import models

from apps.core.sanitizers import sanitize_html
from apps.treasurer.models import Meeting


class MeetingType(models.Model):
    """Reusable meeting type names (e.g., Speaker, Topic, Literature).

    When secretary selects a meeting type, all variations with that type
    will be shown across all blocks.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='meeting_types'
    )
    name = models.CharField(
        max_length=50,
        help_text='Meeting type name, e.g., "Speaker", "Topic", "Literature"'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Meeting Type'
        verbose_name_plural = 'Meeting Types'
        unique_together = ['meeting', 'name']

    def __str__(self):
        return self.name


class FormatModuleConfig(models.Model):
    """Module configuration for Meeting Format."""

    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('x-large', 'Extra Large'),
    ]

    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='format_config'
    )
    public_enabled = models.BooleanField(
        default=True,
        help_text='Allow public access to meeting format'
    )
    share_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        help_text='Token for public URL'
    )

    # Font size settings
    editor_font_size = models.CharField(
        max_length=20,
        choices=FONT_SIZE_CHOICES,
        default='medium',
        help_text='Font size in the content editor'
    )
    display_font_size = models.CharField(
        max_length=20,
        choices=FONT_SIZE_CHOICES,
        default='medium',
        help_text='Font size on public pages'
    )

    # Selected meeting type for tonight
    selected_meeting_type = models.ForeignKey(
        MeetingType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Currently selected meeting type for public display'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Format Configuration'
        verbose_name_plural = 'Format Configurations'

    def __str__(self):
        return f"Format Config: {self.meeting.name}"

    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def get_public_url(self):
        """Return the public URL path for this format."""
        from django.urls import reverse
        return reverse('format_public:view', kwargs={'token': self.share_token})


class FormatBlock(models.Model):
    """A section/block of the meeting format."""
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='format_blocks'
    )
    title = models.CharField(
        max_length=100,
        help_text='Block title, e.g., "Welcome", "Main Content", "Closing"'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Format Block'
        verbose_name_plural = 'Format Blocks'

    def __str__(self):
        return f"{self.title} ({self.meeting.name})"

    def is_rotating(self):
        """Return True if block has multiple active variations."""
        return self.variations.filter(is_active=True).count() > 1

    def get_default_variation(self):
        """Return the default variation for this block."""
        return self.variations.filter(is_default=True, is_active=True).first()

    def get_variation_for_type(self, meeting_type):
        """Return the variation for a specific meeting type, or default."""
        if meeting_type:
            variation = self.variations.filter(
                meeting_type=meeting_type,
                is_active=True
            ).first()
            if variation:
                return variation
        # Fall back to default
        return self.get_default_variation()


class BlockVariation(models.Model):
    """A variation/tab within a block."""
    block = models.ForeignKey(
        FormatBlock,
        on_delete=models.CASCADE,
        related_name='variations'
    )
    meeting_type = models.ForeignKey(
        MeetingType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='variations',
        help_text='Meeting type this variation belongs to (e.g., Speaker, Topic)'
    )
    content = models.TextField(
        blank=True,
        help_text='Rich HTML content. Use [reading_slug] to link to readings.'
    )
    order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(
        default=False,
        help_text='Use this variation when no meeting type is selected'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Block Variation'
        verbose_name_plural = 'Block Variations'

    def __str__(self):
        type_name = self.meeting_type.name if self.meeting_type else 'Default'
        return f"{type_name} ({self.block.title})"

    @property
    def name(self):
        """Return meeting type name for backwards compatibility."""
        return self.meeting_type.name if self.meeting_type else 'Default'

    def save(self, *args, **kwargs):
        # Sanitize HTML content to prevent XSS
        if self.content:
            self.content = sanitize_html(self.content)

        # If this is being set as default, unset others
        if self.is_default:
            BlockVariation.objects.filter(
                block=self.block,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        # If no default exists in this block, make this one the default
        if self.block_id:
            has_default = BlockVariation.objects.filter(
                block=self.block,
                is_default=True
            ).exclude(pk=self.pk).exists()
            if not has_default:
                self.is_default = True

        super().save(*args, **kwargs)


class VariationSchedule(models.Model):
    """Schedule rule for when a variation is active."""
    SCHEDULE_TYPES = [
        ('weekday_occurrence', '1st/2nd/3rd/4th/5th weekday of month'),
        ('day_of_week', 'Every weekday'),
        ('specific_date', 'Specific date'),
    ]

    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    OCCURRENCE_CHOICES = [
        (1, '1st'),
        (2, '2nd'),
        (3, '3rd'),
        (4, '4th'),
        (5, '5th'),
    ]

    variation = models.ForeignKey(
        BlockVariation,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPES
    )
    # For 'weekday_occurrence': "3rd Tuesday"
    occurrence = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=OCCURRENCE_CHOICES,
        help_text='Which occurrence (1st, 2nd, etc.)'
    )
    weekday = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=WEEKDAY_CHOICES,
        help_text='Day of week (0=Monday, 6=Sunday)'
    )
    # For 'specific_date'
    specific_date = models.DateField(
        null=True,
        blank=True,
        help_text='Specific date for this variation'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Variation Schedule'
        verbose_name_plural = 'Variation Schedules'

    def __str__(self):
        if self.schedule_type == 'weekday_occurrence':
            occ = dict(self.OCCURRENCE_CHOICES).get(self.occurrence, '')
            day = dict(self.WEEKDAY_CHOICES).get(self.weekday, '')
            return f"{occ} {day}"
        elif self.schedule_type == 'day_of_week':
            day = dict(self.WEEKDAY_CHOICES).get(self.weekday, '')
            return f"Every {day}"
        elif self.schedule_type == 'specific_date':
            return f"{self.specific_date}"
        return "Schedule"
