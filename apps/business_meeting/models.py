"""
Business Meeting models.

Manages business meeting format templates and meeting notes/minutes.
"""
from django.conf import settings
from django.db import models

from apps.core.sanitizers import sanitize_html


# Default business meeting format template
DEFAULT_FORMAT_CONTENT = """
<h2>Opening</h2>
<p>[Opening prayer or moment of silence]</p>

<h2>Review Previous Minutes</h2>
<p>[Secretary reads or summarizes previous meeting minutes]</p>

<h2>Officer Reports</h2>
<ul>
<li>Treasurer Report</li>
<li>Secretary Report</li>
<li>GSR Report</li>
<li>[Other positions as applicable]</li>
</ul>

<h2>Old Business</h2>
<p>[Unfinished items from previous meetings]</p>

<h2>New Business</h2>
<p>[New items for discussion]</p>

<h2>Closing</h2>
<p>[Closing prayer]</p>
""".strip()


class BusinessMeetingFormat(models.Model):
    """
    The business meeting script/format template.

    One template per meeting (singleton pattern).
    """
    meeting = models.OneToOneField(
        'treasurer.Meeting',
        on_delete=models.CASCADE,
        related_name='business_meeting_format'
    )
    content = models.TextField(
        blank=True,
        default=DEFAULT_FORMAT_CONTENT,
        help_text='The format/script for running business meetings.'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        verbose_name = 'Business Meeting Format'
        verbose_name_plural = 'Business Meeting Formats'

    def __str__(self):
        return f"Business Meeting Format for {self.meeting}"

    @classmethod
    def get_or_create_for_meeting(cls, meeting):
        """Get or create the format for a meeting."""
        obj, created = cls.objects.get_or_create(meeting=meeting)
        return obj

    def save(self, *args, **kwargs):
        # Sanitize HTML content to prevent XSS
        if self.content:
            self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)


class BusinessMeeting(models.Model):
    """
    A single business meeting instance with notes/minutes.
    """
    meeting = models.ForeignKey(
        'treasurer.Meeting',
        on_delete=models.CASCADE,
        related_name='business_meetings'
    )
    date = models.DateField()
    notes = models.TextField(
        blank=True,
        help_text='Meeting notes/minutes.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='business_meetings_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='business_meetings_updated'
    )

    class Meta:
        ordering = ['-date']
        unique_together = ['meeting', 'date']
        verbose_name = 'Business Meeting'
        verbose_name_plural = 'Business Meetings'

    def __str__(self):
        return f"Business Meeting - {self.date}"

    def save(self, *args, **kwargs):
        # Sanitize HTML content to prevent XSS
        if self.notes:
            self.notes = sanitize_html(self.notes)
        super().save(*args, **kwargs)

    def get_notes_preview(self, max_length=100):
        """Return a truncated plain text preview of the notes."""
        import re
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', self.notes)
        # Collapse whitespace
        text = ' '.join(text.split())
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text
