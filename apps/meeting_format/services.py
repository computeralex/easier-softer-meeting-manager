"""
Meeting Format services.
"""
import re
from datetime import date
from typing import Optional

from django.utils.html import escape
from django.urls import reverse

from .models import FormatBlock, BlockVariation, FormatModuleConfig


class FormatService:
    """Service for format-related operations."""

    def __init__(self, meeting):
        self.meeting = meeting

    def get_active_variation(
        self,
        block: FormatBlock,
        for_date: Optional[date] = None
    ) -> Optional[BlockVariation]:
        """Determine which variation is active for a given date."""
        if for_date is None:
            for_date = date.today()

        # Check each variation for matching schedule
        for variation in block.variations.filter(is_active=True).order_by('order'):
            if self._matches_schedule(variation, for_date):
                return variation

        # Fall back to default
        default = block.variations.filter(is_default=True, is_active=True).first()
        if default:
            return default

        # Fall back to first active variation
        return block.variations.filter(is_active=True).first()

    def _matches_schedule(self, variation: BlockVariation, check_date: date) -> bool:
        """Check if any schedule rule matches the date."""
        for schedule in variation.schedules.all():
            if schedule.schedule_type == 'weekday_occurrence':
                if self._is_nth_weekday(check_date, schedule.occurrence, schedule.weekday):
                    return True
            elif schedule.schedule_type == 'day_of_week':
                if check_date.weekday() == schedule.weekday:
                    return True
            elif schedule.schedule_type == 'specific_date':
                if check_date == schedule.specific_date:
                    return True
        return False

    def _is_nth_weekday(self, check_date: date, n: int, weekday: int) -> bool:
        """Check if date is the Nth occurrence of weekday in its month."""
        if check_date.weekday() != weekday:
            return False
        day = check_date.day
        occurrence = (day - 1) // 7 + 1
        return occurrence == n

    def get_format_for_date(self, for_date: Optional[date] = None) -> list:
        """Get full format with active variations for a date."""
        if for_date is None:
            for_date = date.today()

        result = []
        blocks = FormatBlock.objects.filter(
            meeting=self.meeting,
            is_active=True
        ).order_by('order')

        for block in blocks:
            active_variation = self.get_active_variation(block, for_date)
            result.append({
                'block': block,
                'active_variation': active_variation,
                'all_variations': list(block.variations.filter(is_active=True)),
                'is_rotating': block.is_rotating(),
            })

        return result


class ContentRenderer:
    """Renders content with reading bracket syntax replaced."""

    # Pattern to match [reading_slug]
    BRACKET_PATTERN = re.compile(r'\[([a-z0-9_-]+)\]', re.IGNORECASE)

    def __init__(self, meeting, readings_token: Optional[str] = None):
        self.meeting = meeting
        self.readings_token = readings_token
        self._reading_cache = None

    def _get_readings_map(self) -> dict:
        """Get a mapping of slug -> reading display name for this meeting."""
        if self._reading_cache is None:
            from apps.readings.models import Reading
            readings = Reading.objects.filter(
                meeting=self.meeting,
                is_active=True
            ).values('slug', 'title', 'short_name')
            # Use short_name if available, otherwise fall back to title
            self._reading_cache = {
                r['slug']: r['short_name'] if r['short_name'] else r['title']
                for r in readings
            }
        return self._reading_cache

    def render(self, content: str) -> str:
        """Render content, replacing [slug] with reading links."""
        if not content:
            return content

        readings_map = self._get_readings_map()

        def replace_bracket(match):
            slug = match.group(1).lower()
            if slug in readings_map:
                title = readings_map[slug]
                if self.readings_token:
                    url = reverse(
                        'readings_public:detail',
                        kwargs={'token': self.readings_token, 'slug': slug}
                    )
                    return f'<a href="{url}" class="reading-link" target="_blank">{escape(title)}</a>'
                else:
                    # No public token, just show title
                    return f'<span class="reading-ref">{escape(title)}</span>'
            else:
                # Unknown slug, leave as-is
                return match.group(0)

        return self.BRACKET_PATTERN.sub(replace_bracket, content)

    @classmethod
    def get_available_slugs(cls, meeting) -> list:
        """Get list of available reading slugs for help text."""
        from apps.readings.models import Reading
        return list(
            Reading.objects.filter(
                meeting=meeting,
                is_active=True
            ).values_list('slug', flat=True).order_by('title')
        )
