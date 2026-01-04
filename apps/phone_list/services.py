"""
Phone List services.
"""
import csv
import io
from typing import Dict, List, Optional, Tuple

from django.db import models

from .models import PhoneListConfig, Contact, TimeZone


class PhoneListService:
    """Service class for phone list operations."""

    def __init__(self, meeting):
        self.meeting = meeting

    def get_or_create_config(self) -> PhoneListConfig:
        """Get or create phone list configuration."""
        config, _ = PhoneListConfig.objects.get_or_create(meeting=self.meeting)
        return config

    def regenerate_token(self) -> str:
        """Generate a new share token and return it."""
        config = self.get_or_create_config()
        config.regenerate_token()
        return config.share_token

    def get_contacts(self, active_only: bool = False):
        """Get contacts for this meeting."""
        qs = Contact.objects.filter(meeting=self.meeting)
        if active_only:
            qs = qs.filter(is_active=True)
        return qs.select_related('time_zone')

    def parse_csv(self, file) -> Tuple[List[str], List[Dict]]:
        """
        Parse CSV file and return headers and rows.
        Returns: (headers, rows) where rows is list of dicts
        """
        # Read file content
        if hasattr(file, 'read'):
            content = file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8-sig')  # Handle BOM
        else:
            content = file

        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames or []
        rows = list(reader)

        return headers, rows

    def auto_detect_mapping(self, headers: List[str]) -> Dict[str, str]:
        """
        Auto-detect column mapping based on common header names.
        Returns: dict mapping field names to CSV headers
        """
        mapping = {}
        header_lower = {h.lower().strip(): h for h in headers}

        # Common variations for each field
        field_variations = {
            'name': ['name', 'full name', 'fullname', 'contact', 'member'],
            'phone': ['phone', 'phone number', 'mobile', 'cell', 'telephone', 'tel'],
            'email': ['email', 'e-mail', 'email address'],
            'has_whatsapp': ['whatsapp', 'has whatsapp', 'whats app'],
            'available_to_sponsor': ['sponsor', 'available to sponsor', 'sponsors', 'can sponsor'],
            'sobriety_date': ['sobriety date', 'sobriety', 'clean date', 'sober date'],
            'time_zone': ['timezone', 'time zone', 'tz', 'zone'],
            'notes': ['notes', 'note', 'comments', 'comment'],
        }

        for field, variations in field_variations.items():
            for var in variations:
                if var in header_lower:
                    mapping[field] = header_lower[var]
                    break

        return mapping

    def import_contacts(
        self,
        rows: List[Dict],
        mapping: Dict[str, str],
        mode: str = 'add',
        tz_resolutions: Optional[Dict] = None,
        meeting=None
    ) -> Tuple[int, int, List[str], int]:
        """
        Import contacts from CSV data.

        Args:
            rows: List of row dicts from CSV
            mapping: Dict mapping Contact fields to CSV column names
            mode: 'add' (new only), 'update' (update existing by name), 'replace' (delete all first)
            tz_resolutions: Dict of unknown timezone resolutions
            meeting: Meeting instance for creating new time zones

        Returns:
            (added_count, updated_count, errors, tz_created_count)
        """
        added = 0
        updated = 0
        errors = []
        tz_created = 0
        tz_resolutions = tz_resolutions or {}
        meeting = meeting or self.meeting

        # Get time zones for lookup (global and meeting-specific)
        time_zones = {}
        for tz in TimeZone.objects.filter(
            models.Q(meeting=meeting) | models.Q(meeting__isnull=True),
            is_active=True
        ):
            time_zones[tz.code.upper()] = tz

        # Process timezone resolutions - create new ones first
        for tz_value, resolution in tz_resolutions.items():
            if resolution.get('action') == 'create':
                display_name = resolution.get('create_name', '').strip() or tz_value
                # Get max order for new timezone
                max_tz_order = TimeZone.objects.filter(
                    models.Q(meeting=meeting) | models.Q(meeting__isnull=True)
                ).aggregate(max_order=models.Max('order'))['max_order'] or 0
                new_tz = TimeZone.objects.create(
                    meeting=meeting,
                    code=tz_value,
                    display_name=display_name,
                    order=max_tz_order + 1
                )
                time_zones[tz_value.upper()] = new_tz
                tz_created += 1
            elif resolution.get('action') == 'map':
                map_to_id = resolution.get('map_to', '')
                if map_to_id:
                    try:
                        existing_tz = TimeZone.objects.get(pk=int(map_to_id))
                        time_zones[tz_value.upper()] = existing_tz
                    except (TimeZone.DoesNotExist, ValueError):
                        pass

        if mode == 'replace':
            Contact.objects.filter(meeting=self.meeting).delete()

        # Get max display order
        max_order = Contact.objects.filter(meeting=self.meeting).aggregate(
            max_order=models.Max('display_order')
        )['max_order'] or 0

        for i, row in enumerate(rows, start=1):
            try:
                # Get name (required)
                name_col = mapping.get('name')
                if not name_col or not row.get(name_col, '').strip():
                    errors.append(f"Row {i}: Name is required")
                    continue

                name = row[name_col].strip()

                # Build contact data
                data = {
                    'name': name,
                    'phone': row.get(mapping.get('phone', ''), '').strip(),
                    'email': row.get(mapping.get('email', ''), '').strip(),
                    'notes': row.get(mapping.get('notes', ''), '').strip(),
                }

                # Boolean fields
                whatsapp_val = row.get(mapping.get('has_whatsapp', ''), '').strip().lower()
                data['has_whatsapp'] = whatsapp_val in ('yes', 'true', '1', 'y', 'x')

                sponsor_val = row.get(mapping.get('available_to_sponsor', ''), '').strip().lower()
                data['available_to_sponsor'] = sponsor_val in ('yes', 'true', '1', 'y', 'x')

                # Sobriety date
                sobriety_str = row.get(mapping.get('sobriety_date', ''), '').strip()
                if sobriety_str:
                    from dateutil import parser
                    try:
                        data['sobriety_date'] = parser.parse(sobriety_str).date()
                    except (ValueError, TypeError):
                        pass  # Skip invalid dates

                # Time zone
                tz_str = row.get(mapping.get('time_zone', ''), '').strip()
                if tz_str:
                    tz_upper = tz_str.upper()
                    if tz_upper in time_zones:
                        data['time_zone'] = time_zones[tz_upper]
                    else:
                        # Check if this should go to "other" field
                        resolution = tz_resolutions.get(tz_str, {})
                        if resolution.get('action') == 'other':
                            data['time_zone_other'] = tz_str

                # Create or update
                if mode == 'update':
                    contact, created = Contact.objects.update_or_create(
                        meeting=self.meeting,
                        name=name,
                        defaults=data
                    )
                    if created:
                        contact.display_order = max_order + added + 1
                        contact.save(update_fields=['display_order'])
                        added += 1
                    else:
                        updated += 1
                else:
                    # Add mode or replace mode
                    max_order += 1
                    data['display_order'] = max_order
                    Contact.objects.create(meeting=self.meeting, **data)
                    added += 1

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        return added, updated, errors, tz_created

    def generate_pdf(self, meeting_name: str, sobriety_term: str = 'Sobriety') -> bytes:
        """
        Generate PDF phone list based on config settings.

        Args:
            meeting_name: Name of the meeting for header
            sobriety_term: Term to use for sobriety date column

        Returns:
            PDF file as bytes
        """
        from weasyprint import HTML

        config = self.get_or_create_config()
        contacts = self.get_contacts(active_only=True)

        if config.pdf_layout == 'two_column':
            html = self._generate_two_column_html(contacts, config, meeting_name, sobriety_term)
        else:
            html = self._generate_table_html(contacts, config, meeting_name, sobriety_term)

        return HTML(string=html).write_pdf()

    def _generate_table_html(self, contacts, config, meeting_name: str, sobriety_term: str) -> str:
        """Generate table layout HTML for PDF."""
        font_size = config.pdf_font_size

        # Build column headers and data
        columns = [('Name / Sponsor?', 'name')]
        if config.pdf_show_phone:
            columns.append(('Phone / WhatsApp?', 'phone'))
        if config.pdf_show_email:
            columns.append(('Email', 'email'))
        if config.pdf_show_time_zone:
            columns.append(('Time Zone', 'time_zone'))
        if config.pdf_show_sobriety:
            columns.append((sobriety_term.title(), 'sobriety'))

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @page {{
                    size: letter;
                    margin: 0.5in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: {font_size}pt;
                    line-height: 1.3;
                    color: #1a1a1a;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 15px;
                }}
                .header h1 {{
                    font-size: {font_size + 5}pt;
                    margin: 0 0 3px 0;
                    color: #000;
                }}
                .header p {{
                    color: #444;
                    margin: 0;
                    font-size: {font_size - 1}pt;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid #999;
                    padding: 3px 6px;
                    text-align: left;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }}
                th {{
                    background: #e0e0e0;
                    font-weight: bold;
                    font-size: {font_size - 1}pt;
                    color: #000;
                }}
                tr:nth-child(even) {{
                    background: #f5f5f5;
                }}
                .sponsor-badge {{
                    background: #146c2e;
                    color: white;
                    padding: 1px 5px;
                    border-radius: 3px;
                    font-size: {font_size - 2}pt;
                    margin-left: 3px;
                }}
                .whatsapp {{
                    color: #146c2e;
                    font-weight: bold;
                    font-size: {font_size - 2}pt;
                    margin-left: 3px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 15px;
                    font-size: {font_size - 2}pt;
                    color: #444;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{meeting_name}</h1>
                <p>Phone List</p>
            </div>
            <table>
                <thead>
                    <tr>
        """

        for header, _ in columns:
            html += f"<th>{header}</th>"

        html += "</tr></thead><tbody>"

        for contact in contacts:
            html += "<tr>"
            for _, col_type in columns:
                if col_type == 'name':
                    val = contact.name
                    if contact.available_to_sponsor:
                        val += ' <span class="sponsor-badge">S</span>'
                    html += f"<td>{val}</td>"
                elif col_type == 'phone':
                    val = contact.phone or '-'
                    if contact.has_whatsapp and contact.phone:
                        val += ' <span class="whatsapp">W</span>'
                    html += f"<td>{val}</td>"
                elif col_type == 'email':
                    html += f"<td>{contact.email or '-'}</td>"
                elif col_type == 'time_zone':
                    tz = contact.time_zone.display_name if contact.time_zone else contact.time_zone_other or '-'
                    html += f"<td>{tz}</td>"
                elif col_type == 'sobriety':
                    val = contact.sobriety_date.strftime('%m/%d/%Y') if contact.sobriety_date else '-'
                    html += f"<td>{val}</td>"
            html += "</tr>"

        html += "</tbody></table>"

        if config.pdf_footer_text:
            html += f'<div class="footer">{config.pdf_footer_text}</div>'

        html += "</body></html>"
        return html

    def _generate_two_column_html(self, contacts, config, meeting_name: str, sobriety_term: str) -> str:
        """Generate two-column list layout HTML for PDF."""
        font_size = config.pdf_font_size

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @page {{
                    size: letter;
                    margin: 0.5in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: {font_size}pt;
                    line-height: 1.2;
                    color: #1a1a1a;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 15px;
                }}
                .header h1 {{
                    font-size: {font_size + 4}pt;
                    margin: 0;
                    color: #000;
                }}
                .columns {{
                    column-count: 2;
                    column-gap: 20px;
                }}
                .contact {{
                    break-inside: avoid;
                    padding: 4px 0;
                    border-bottom: 1px solid #ccc;
                }}
                .name {{
                    font-weight: bold;
                }}
                .sponsor-badge {{
                    background: #146c2e;
                    color: white;
                    padding: 0 4px;
                    border-radius: 2px;
                    font-size: {font_size - 2}pt;
                    margin-left: 4px;
                }}
                .details {{
                    color: #333;
                    font-size: {font_size - 1}pt;
                }}
                .whatsapp {{
                    color: #146c2e;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 15px;
                    font-size: {font_size - 2}pt;
                    color: #444;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{meeting_name}</h1>
            </div>
            <div class="columns">
        """

        for contact in contacts:
            html += '<div class="contact">'
            html += f'<span class="name">{contact.name}</span>'
            if contact.available_to_sponsor:
                html += '<span class="sponsor-badge">S</span>'
            html += '<br><span class="details">'

            parts = []
            if config.pdf_show_phone and contact.phone:
                phone_part = contact.phone
                if contact.has_whatsapp:
                    phone_part += ' <span class="whatsapp">(W)</span>'
                parts.append(phone_part)

            if config.pdf_show_email and contact.email:
                parts.append(contact.email)

            if config.pdf_show_time_zone:
                tz = contact.time_zone.display_name if contact.time_zone else contact.time_zone_other
                if tz:
                    parts.append(tz)

            if config.pdf_show_sobriety and contact.sobriety_date:
                parts.append(contact.sobriety_date.strftime('%m/%d/%Y'))

            html += ' | '.join(parts) if parts else '-'
            html += '</span></div>'

        html += "</div>"

        if config.pdf_footer_text:
            html += f'<div class="footer">{config.pdf_footer_text}</div>'

        html += "</body></html>"
        return html

    def export_csv(self, sobriety_term: str = 'Sobriety') -> str:
        """
        Export contacts to CSV format.

        Args:
            sobriety_term: Term to use for sobriety date column header

        Returns:
            CSV content as string
        """
        contacts = self.get_contacts(active_only=True)

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Name',
            'Phone',
            'WhatsApp',
            'Email',
            'Available to Sponsor',
            f'{sobriety_term.title()} Date',
            'Time Zone',
            'Notes'
        ])

        # Write data
        for contact in contacts:
            tz = contact.time_zone.display_name if contact.time_zone else contact.time_zone_other or ''
            writer.writerow([
                contact.name,
                contact.phone,
                'Yes' if contact.has_whatsapp else 'No',
                contact.email,
                'Yes' if contact.available_to_sponsor else 'No',
                contact.sobriety_date.strftime('%Y-%m-%d') if contact.sobriety_date else '',
                tz,
                contact.notes
            ])

        return output.getvalue()
