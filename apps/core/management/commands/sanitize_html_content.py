"""
Management command to sanitize existing HTML content in the database.

This command processes all models with rich text HTML fields and sanitizes
them to remove potential XSS vulnerabilities.

Usage:
    # Dry run - see what would be changed
    python manage.py sanitize_html_content --dry-run

    # Actually sanitize content
    python manage.py sanitize_html_content

    # Verbose output
    python manage.py sanitize_html_content -v 2
"""
from django.core.management.base import BaseCommand

from apps.core.sanitizers import sanitize_html


class Command(BaseCommand):
    help = 'Sanitize all existing HTML content in the database to prevent XSS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually modifying data',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbosity = options['verbosity']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made\n'))

        total_changed = 0
        total_checked = 0

        # Process each model with HTML content
        total_changed += self._process_readings(dry_run, verbosity)
        total_changed += self._process_block_variations(dry_run, verbosity)
        total_changed += self._process_business_meetings(dry_run, verbosity)
        total_changed += self._process_business_meeting_formats(dry_run, verbosity)
        total_changed += self._process_website_pages(dry_run, verbosity)

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN: Would update {total_changed} records'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully sanitized {total_changed} records'
            ))

    def _process_readings(self, dry_run, verbosity):
        """Sanitize Reading.content"""
        from apps.readings.models import Reading

        changed = 0
        for obj in Reading.objects.all():
            if not obj.content:
                continue

            sanitized = sanitize_html(obj.content)
            if sanitized != obj.content:
                changed += 1
                if verbosity >= 2:
                    self.stdout.write(f'  Reading "{obj.title}" (id={obj.pk}): content changed')
                if not dry_run:
                    obj.content = sanitized
                    obj.save(update_fields=['content', 'updated_at'])

        self.stdout.write(f'Readings: {changed} records {"would be " if dry_run else ""}updated')
        return changed

    def _process_block_variations(self, dry_run, verbosity):
        """Sanitize BlockVariation.content"""
        from apps.meeting_format.models import BlockVariation

        changed = 0
        for obj in BlockVariation.objects.all():
            if not obj.content:
                continue

            sanitized = sanitize_html(obj.content)
            if sanitized != obj.content:
                changed += 1
                if verbosity >= 2:
                    self.stdout.write(f'  BlockVariation (id={obj.pk}): content changed')
                if not dry_run:
                    obj.content = sanitized
                    obj.save(update_fields=['content', 'updated_at'])

        self.stdout.write(f'BlockVariations: {changed} records {"would be " if dry_run else ""}updated')
        return changed

    def _process_business_meetings(self, dry_run, verbosity):
        """Sanitize BusinessMeeting.notes"""
        from apps.business_meeting.models import BusinessMeeting

        changed = 0
        for obj in BusinessMeeting.objects.all():
            if not obj.notes:
                continue

            sanitized = sanitize_html(obj.notes)
            if sanitized != obj.notes:
                changed += 1
                if verbosity >= 2:
                    self.stdout.write(f'  BusinessMeeting (id={obj.pk}): notes changed')
                if not dry_run:
                    obj.notes = sanitized
                    obj.save(update_fields=['notes', 'updated_at'])

        self.stdout.write(f'BusinessMeetings: {changed} records {"would be " if dry_run else ""}updated')
        return changed

    def _process_business_meeting_formats(self, dry_run, verbosity):
        """Sanitize BusinessMeetingFormat.content"""
        from apps.business_meeting.models import BusinessMeetingFormat

        changed = 0
        for obj in BusinessMeetingFormat.objects.all():
            if not obj.content:
                continue

            sanitized = sanitize_html(obj.content)
            if sanitized != obj.content:
                changed += 1
                if verbosity >= 2:
                    self.stdout.write(f'  BusinessMeetingFormat (id={obj.pk}): content changed')
                if not dry_run:
                    obj.content = sanitized
                    obj.save(update_fields=['content', 'updated_at'])

        self.stdout.write(f'BusinessMeetingFormats: {changed} records {"would be " if dry_run else ""}updated')
        return changed

    def _process_website_pages(self, dry_run, verbosity):
        """Sanitize WebsitePage.rendered_html"""
        from apps.website.models import WebsitePage

        changed = 0
        for obj in WebsitePage.objects.all():
            if not obj.rendered_html:
                continue

            sanitized = sanitize_html(obj.rendered_html)
            if sanitized != obj.rendered_html:
                changed += 1
                if verbosity >= 2:
                    self.stdout.write(f'  WebsitePage "{obj.title}" (id={obj.pk}): rendered_html changed')
                if not dry_run:
                    obj.rendered_html = sanitized
                    obj.save(update_fields=['rendered_html', 'updated_at'])

        self.stdout.write(f'WebsitePages: {changed} records {"would be " if dry_run else ""}updated')
        return changed
