"""
Server-side renderer for Puck JSON content.

Converts Puck's JSON data format to HTML using Django templates.
This allows public pages to be served without client-side JavaScript.

Security: All output is sanitized via apps.core.sanitizers before
being marked safe for template rendering.
"""
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from typing import Any

from apps.core.sanitizers import sanitize_html


# Map component types to their templates
COMPONENT_TEMPLATES = {
    'Hero': 'website/puck_components/hero.html',
    'Text': 'website/puck_components/text.html',
    'Image': 'website/puck_components/image.html',
    'TwoColumn': 'website/puck_components/two_column.html',
    'Card': 'website/puck_components/card.html',
    'Button': 'website/puck_components/button.html',
    'Spacer': 'website/puck_components/spacer.html',
}


def render_puck_content(puck_data: dict) -> str:
    """
    Render Puck JSON to HTML on the server.

    Args:
        puck_data: The Puck data object with 'content' and 'root' keys

    Returns:
        Sanitized HTML string (safe for template rendering)
    """
    if not puck_data:
        return ''

    content = puck_data.get('content', [])
    zones = puck_data.get('zones', {})

    html_parts = []
    for item in content:
        rendered = render_component(item, zones)
        if rendered:
            html_parts.append(rendered)

    # Sanitize the combined HTML to prevent XSS
    raw_html = '\n'.join(html_parts)
    return sanitize_html(raw_html)


def render_component(item: dict, zones: dict) -> str:
    """
    Render a single Puck component to HTML.

    Args:
        item: Component data with 'type' and 'props'
        zones: Dictionary of nested zones for layout components

    Returns:
        Rendered HTML string
    """
    component_type = item.get('type')
    props = item.get('props', {})
    component_id = props.get('id', '')

    template = COMPONENT_TEMPLATES.get(component_type)
    if not template:
        return f'<!-- Unknown component: {component_type} -->'

    # For layout components, render nested zones
    if component_type == 'TwoColumn':
        props = enrich_layout_props(props, component_id, zones)

    try:
        return render_to_string(template, {'props': props})
    except Exception as e:
        return f'<!-- Error rendering {component_type}: {e} -->'


def enrich_layout_props(props: dict, component_id: str, zones: dict) -> dict:
    """
    Enrich layout component props with rendered nested content.

    Args:
        props: Component props
        component_id: The component's unique ID
        zones: Dictionary of zone content

    Returns:
        Props with 'left_content' and 'right_content' HTML
    """
    enriched = dict(props)

    # Zone keys are formatted as "component_id:zone_name"
    left_zone_key = f'{component_id}:left'
    right_zone_key = f'{component_id}:right'

    left_items = zones.get(left_zone_key, [])
    right_items = zones.get(right_zone_key, [])

    # Recursively render nested components
    left_html = []
    for item in left_items:
        rendered = render_component(item, zones)
        if rendered:
            left_html.append(rendered)

    right_html = []
    for item in right_items:
        rendered = render_component(item, zones)
        if rendered:
            right_html.append(rendered)

    # Sanitize nested content for XSS protection
    enriched['left_content'] = mark_safe(sanitize_html('\n'.join(left_html)))
    enriched['right_content'] = mark_safe(sanitize_html('\n'.join(right_html)))

    return enriched
