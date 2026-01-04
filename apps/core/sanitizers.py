"""
HTML sanitization utilities for user-generated content.

Uses nh3 (Rust-based HTML sanitizer) to prevent XSS attacks while
preserving safe formatting, tables, and whitelisted embeds.
"""
import re
from urllib.parse import urlparse

import nh3


# Allowed tags for rich text content (includes tables + iframes for embeds)
ALLOWED_TAGS = {
    # Basic formatting
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 'sub', 'sup',
    # Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Lists
    'ul', 'ol', 'li',
    # Block elements
    'blockquote', 'pre', 'code',
    # Links and media
    'a', 'img',
    # Tables
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
    # Layout
    'hr', 'span', 'div',
    # Embeds (validated separately)
    'iframe',
    # Figures
    'figure', 'figcaption',
}

# Whitelist of allowed iframe sources for video embeds
ALLOWED_IFRAME_HOSTS = {
    'www.youtube.com',
    'youtube.com',
    'www.youtube-nocookie.com',
    'player.vimeo.com',
    'vimeo.com',
}

# Allowed attributes per tag
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title', 'target', 'class'},  # rel set via link_rel param
    'img': {'src', 'alt', 'title', 'width', 'height', 'class', 'loading'},
    'iframe': {'src', 'width', 'height', 'frameborder', 'allowfullscreen',
               'allow', 'title', 'class'},
    'span': {'class', 'style'},
    'div': {'class', 'style'},
    'p': {'class', 'style'},
    'td': {'colspan', 'rowspan', 'class', 'style'},
    'th': {'colspan', 'rowspan', 'class', 'scope', 'style'},
    'col': {'span'},
    'table': {'class', 'style'},
    'tr': {'class'},
    'thead': {'class'},
    'tbody': {'class'},
    'tfoot': {'class'},
    'ul': {'class'},
    'ol': {'class', 'start', 'type'},
    'li': {'class'},
    'blockquote': {'class'},
    'pre': {'class'},
    'code': {'class'},
    'h1': {'class'},
    'h2': {'class'},
    'h3': {'class'},
    'h4': {'class'},
    'h5': {'class'},
    'h6': {'class'},
    '*': {'class'},  # Allow class on all elements as fallback
}

# Safe URL schemes
ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto'}


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML content, removing dangerous tags and attributes.

    This function:
    1. Uses nh3 to strip unsafe HTML elements and attributes
    2. Validates iframe sources against a whitelist
    3. Ensures all links have safe rel attributes

    Args:
        html: Raw HTML string from user input

    Returns:
        Sanitized HTML string safe for rendering with |safe filter
    """
    if not html:
        return html

    # First pass: nh3 sanitization
    cleaned = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel="noopener noreferrer",
        url_schemes=ALLOWED_URL_SCHEMES,
    )

    # Second pass: validate iframe sources
    cleaned = _sanitize_iframes(cleaned)

    return cleaned


def _sanitize_iframes(html: str) -> str:
    """
    Remove iframes with non-whitelisted sources.

    Only allows iframes from trusted video hosting platforms
    (YouTube, Vimeo) to prevent malicious embeds.

    Args:
        html: HTML string potentially containing iframes

    Returns:
        HTML with unauthorized iframes removed
    """
    def check_iframe(match):
        iframe_html = match.group(0)
        src_match = re.search(r'src=["\']([^"\']+)["\']', iframe_html)

        if not src_match:
            return ''  # No src attribute, remove iframe

        src = src_match.group(1)
        try:
            parsed = urlparse(src)
            if parsed.netloc in ALLOWED_IFRAME_HOSTS:
                return iframe_html  # Allowed source, keep it
        except Exception:
            pass  # Invalid URL, remove

        return ''  # Not allowed, remove iframe

    # Match <iframe ...>...</iframe> or self-closing <iframe ... />
    pattern = r'<iframe[^>]*(?:>.*?</iframe>|/>)'
    return re.sub(pattern, check_iframe, html, flags=re.DOTALL | re.IGNORECASE)


def sanitize_plain_text(text: str) -> str:
    """
    Strip all HTML from text, returning plain text only.

    Use this for fields that should never contain HTML.

    Args:
        text: String potentially containing HTML

    Returns:
        Plain text with all HTML removed
    """
    if not text:
        return text

    return nh3.clean(text, tags=set())
