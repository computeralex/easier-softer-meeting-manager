"""
Website models for public-facing content configuration.
"""
from django.db import models
from django.urls import reverse

from apps.core.sanitizers import sanitize_html


class WebsiteModuleConfig(models.Model):
    """
    Website configuration - singleton per meeting.
    Controls public site appearance and module visibility.
    """
    meeting = models.OneToOneField(
        'treasurer.Meeting',
        on_delete=models.CASCADE,
        related_name='website_config'
    )

    # Home page configuration
    HOME_PAGE_CHOICES = [
        ('format', 'Meeting Format'),
        ('page', 'CMS Page'),
    ]
    home_page_type = models.CharField(
        max_length=10,
        choices=HOME_PAGE_CHOICES,
        default='format'
    )
    home_cms_page = models.ForeignKey(
        'WebsitePage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='CMS page to show as home (when home_page_type=page)'
    )

    # Module visibility on public site
    public_format_enabled = models.BooleanField(
        default=True,
        help_text='Show Meeting Format in public navigation'
    )
    public_readings_enabled = models.BooleanField(
        default=True,
        help_text='Show Readings in public navigation'
    )
    public_phone_list_enabled = models.BooleanField(
        default=False,
        help_text='Show Phone List in public navigation'
    )
    public_treasurer_enabled = models.BooleanField(
        default=False,
        help_text='Show Treasurer Reports in public navigation'
    )

    # Navigation settings
    show_login_link = models.BooleanField(
        default=True,
        help_text='Show login link in public navigation'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Website Configuration'
        verbose_name_plural = 'Website Configurations'

    def __str__(self):
        return f"Website Config for {self.meeting.name}"

    @classmethod
    def get_instance(cls):
        """Get the singleton website config, creating if needed."""
        from apps.treasurer.models import Meeting
        meeting = Meeting.objects.first()
        if not meeting:
            meeting = Meeting.objects.create(name='My Meeting')
        obj, _ = cls.objects.get_or_create(meeting=meeting)
        return obj


class WebsitePage(models.Model):
    """
    CMS page with Puck visual editor content.
    Groups can create custom pages like About Us, Contact, etc.
    """
    meeting = models.ForeignKey(
        'treasurer.Meeting',
        on_delete=models.CASCADE,
        related_name='website_pages'
    )

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # SEO fields
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text='SEO title (defaults to page title if blank)'
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text='SEO description for search engines'
    )
    featured_image = models.CharField(
        max_length=500,
        blank=True,
        help_text='Featured image path'
    )

    # Puck editor stores content as JSON
    content = models.JSONField(
        default=dict,
        blank=True,
        help_text='Puck editor JSON content'
    )

    # Cached rendered HTML for public display
    rendered_html = models.TextField(
        blank=True,
        help_text='Cached HTML render of Puck content'
    )

    is_published = models.BooleanField(default=True)
    show_in_nav = models.BooleanField(
        default=True,
        help_text='Show in public navigation menu'
    )
    nav_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nav_order', 'title']
        unique_together = ['meeting', 'slug']
        verbose_name = 'Website Page'
        verbose_name_plural = 'Website Pages'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('website:page', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        # Re-render HTML when content changes, then sanitize for XSS protection
        if self.content:
            from apps.website.puck.renderer import render_puck_content
            raw_html = render_puck_content(self.content)
            # Defense in depth: sanitize even after renderer sanitizes
            self.rendered_html = sanitize_html(raw_html)
        super().save(*args, **kwargs)
