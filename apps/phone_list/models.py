"""
Phone List models.
"""
import secrets
from django.db import models

from apps.treasurer.models import Meeting


class TimeZone(models.Model):
    """
    Time zone options for contacts.
    Seeded with US time zones, more can be added via settings.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='time_zones',
        null=True,
        blank=True
    )
    code = models.CharField(max_length=20)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'code']

    def __str__(self):
        return self.display_name


class PhoneListConfig(models.Model):
    """
    Per-meeting phone list configuration.
    """
    LAYOUT_CHOICES = [
        ('table', 'Table'),
        ('two_column', 'Two-Column List'),
    ]
    FONT_SIZE_CHOICES = [
        (8, '8pt (Very Compact)'),
        (9, '9pt (Compact)'),
        (10, '10pt (Standard)'),
        (11, '11pt (Large)'),
        (12, '12pt (Extra Large)'),
    ]

    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='phone_list_config'
    )
    share_token = models.CharField(max_length=64, unique=True, blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the public phone list is accessible'
    )

    # PDF Export Settings
    pdf_layout = models.CharField(
        max_length=20,
        choices=LAYOUT_CHOICES,
        default='table',
        help_text='Layout style for PDF export'
    )
    pdf_font_size = models.PositiveSmallIntegerField(
        choices=FONT_SIZE_CHOICES,
        default=9,
        help_text='Font size for PDF export'
    )
    pdf_show_phone = models.BooleanField(default=True, verbose_name='Phone / WhatsApp')
    pdf_show_email = models.BooleanField(default=True, verbose_name='Email')
    pdf_show_time_zone = models.BooleanField(default=True, verbose_name='Time Zone')
    pdf_show_sobriety = models.BooleanField(default=False, verbose_name='Sobriety Date')
    pdf_footer_text = models.CharField(
        max_length=500,
        blank=True,
        default='This phone list is for meeting members only. Please respect everyone\'s privacy.',
        help_text='Footer text on PDF (leave blank for none)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Phone List Configuration'

    def __str__(self):
        return f"Phone List Config for {self.meeting.name}"

    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def regenerate_token(self):
        """Generate a new share token."""
        self.share_token = secrets.token_urlsafe(32)
        self.save(update_fields=['share_token', 'updated_at'])


class Contact(models.Model):
    """
    Contact entry in the phone list.
    """
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    has_whatsapp = models.BooleanField(default=False)
    email = models.EmailField(blank=True)
    available_to_sponsor = models.BooleanField(default=False)
    sobriety_date = models.DateField(null=True, blank=True)
    time_zone = models.ForeignKey(
        TimeZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    time_zone_other = models.CharField(
        max_length=50,
        blank=True,
        help_text='Custom time zone if not in list'
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this contact appears on the public list'
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name
