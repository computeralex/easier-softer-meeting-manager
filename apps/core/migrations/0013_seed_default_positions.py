"""
Seed default service positions with appropriate module permissions.
"""
from django.db import migrations


DEFAULT_POSITIONS = [
    {
        'name': 'secretary',
        'display_name': 'Secretary',
        'description': 'Records meeting minutes and handles correspondence',
        'term_months': 6,
        'sobriety_requirement': '6 months',
        'can_manage_users': True,
        'module_permissions': {
            'business_meeting': 'write',
            'positions': 'read',
        },
        'show_on_public_site': True,
        'warn_on_multiple_holders': True,
        'order': 10,
    },
    {
        'name': 'treasurer',
        'display_name': 'Treasurer',
        'description': 'Manages group finances and 7th Tradition',
        'term_months': 6,
        'sobriety_requirement': '1 year',
        'can_manage_users': False,
        'module_permissions': {
            'treasurer': 'write',
        },
        'show_on_public_site': True,
        'warn_on_multiple_holders': True,
        'order': 20,
    },
    {
        'name': 'group_rep',
        'display_name': 'Group Rep (GSR)',
        'description': 'Represents the group at district and area meetings',
        'term_months': 12,
        'sobriety_requirement': '2 years',
        'can_manage_users': False,
        'module_permissions': {
            'business_meeting': 'read',
        },
        'show_on_public_site': True,
        'warn_on_multiple_holders': True,
        'order': 30,
    },
    {
        'name': 'phone_list_coordinator',
        'display_name': 'Phone List Coordinator',
        'description': 'Maintains the group phone list',
        'term_months': 6,
        'sobriety_requirement': '3 months',
        'can_manage_users': False,
        'module_permissions': {
            'phone_list': 'write',
        },
        'show_on_public_site': True,
        'warn_on_multiple_holders': True,
        'order': 40,
    },
    {
        'name': 'birthday_chairperson',
        'display_name': 'Birthday Chairperson',
        'description': 'Coordinates sobriety birthday celebrations',
        'term_months': 6,
        'sobriety_requirement': '3 months',
        'can_manage_users': False,
        'module_permissions': {},
        'show_on_public_site': True,
        'warn_on_multiple_holders': True,
        'order': 50,
    },
    {
        'name': 'literature_chairperson',
        'display_name': 'Literature Chairperson',
        'description': 'Manages group literature inventory and sales',
        'term_months': 6,
        'sobriety_requirement': '3 months',
        'can_manage_users': False,
        'module_permissions': {
            'readings': 'write',
        },
        'show_on_public_site': True,
        'warn_on_multiple_holders': True,
        'order': 60,
    },
    {
        'name': 'tech_host',
        'display_name': 'Tech Host',
        'description': 'Manages online meeting technology (Zoom, etc.)',
        'term_months': 6,
        'sobriety_requirement': '30 days',
        'can_manage_users': False,
        'module_permissions': {
            'meeting_format': 'write',
            'website': 'write',
        },
        'show_on_public_site': True,
        'warn_on_multiple_holders': False,  # Multiple tech hosts common
        'order': 70,
    },
]


def seed_positions(apps, schema_editor):
    ServicePosition = apps.get_model('core', 'ServicePosition')
    for pos_data in DEFAULT_POSITIONS:
        ServicePosition.objects.get_or_create(
            name=pos_data['name'],
            defaults=pos_data
        )


def remove_positions(apps, schema_editor):
    ServicePosition = apps.get_model('core', 'ServicePosition')
    position_names = [p['name'] for p in DEFAULT_POSITIONS]
    # Only delete if they have no assignment history
    for name in position_names:
        pos = ServicePosition.objects.filter(name=name).first()
        if pos and not pos.assignments.exists():
            pos.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_add_logo_field'),
    ]

    operations = [
        migrations.RunPython(seed_positions, remove_positions),
    ]
