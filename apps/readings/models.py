"""
Readings models.
"""
import secrets
from django.db import models
from django.utils.text import slugify

from apps.core.sanitizers import sanitize_html
from apps.treasurer.models import Meeting


class ReadingCategory(models.Model):
    """Category for grouping readings."""
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='reading_categories'
    )
    name = models.CharField(max_length=100)  # "Prayers", "Steps", "Traditions"
    slug = models.SlugField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['meeting', 'slug']
        ordering = ['order', 'name']
        verbose_name_plural = 'Reading categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            base_slug = self.slug
            counter = 1
            while ReadingCategory.objects.filter(meeting=self.meeting, slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class Reading(models.Model):
    """A reading/prayer/text used in meetings."""
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='readings'
    )
    title = models.CharField(max_length=200)  # "Serenity Prayer", "How It Works"
    short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text='Short name for use in meeting format links (e.g., "12 Traditions")'
    )
    slug = models.SlugField(max_length=200)   # URL-friendly: "serenity-prayer"
    content = models.TextField()              # Rich HTML from Quill editor

    # Organization
    category = models.ForeignKey(
        ReadingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='readings'
    )

    # Metadata
    notes = models.TextField(
        blank=True,
        help_text='Internal notes (not shown publicly)'
    )
    copyright_notice = models.TextField(
        blank=True,
        help_text='Copyright notice shown at bottom of reading (e.g., source attribution)'
    )

    # Display order within category
    order = models.PositiveIntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)
    noindex = models.BooleanField(
        default=False,
        help_text='Prevent search engines from indexing this reading'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['meeting', 'slug']
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Sanitize HTML content to prevent XSS
        if self.content:
            self.content = sanitize_html(self.content)

        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure uniqueness
            base_slug = self.slug
            counter = 1
            while Reading.objects.filter(meeting=self.meeting, slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class ReadingsModuleConfig(models.Model):
    """Configuration for the Readings module."""

    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('x-large', 'Extra Large'),
    ]

    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='readings_config'
    )

    # Public access
    public_enabled = models.BooleanField(
        default=True,
        help_text='Allow public viewing of readings'
    )
    share_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        help_text='Token for public share link'
    )

    # Display options
    show_sources = models.BooleanField(
        default=True,
        help_text='Show source citations on public pages'
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Readings Configuration'

    def __str__(self):
        return f"Readings Config for {self.meeting.name}"

    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def regenerate_token(self):
        """Generate a new share token."""
        self.share_token = secrets.token_urlsafe(32)
        self.save(update_fields=['share_token', 'updated_at'])
