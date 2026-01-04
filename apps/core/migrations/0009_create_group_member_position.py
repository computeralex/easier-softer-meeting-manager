"""
Create the default "Group Member" position.
"""
from django.db import migrations


def create_group_member(apps, schema_editor):
    ServicePosition = apps.get_model('core', 'ServicePosition')
    ServicePosition.objects.get_or_create(
        name='group_member',
        defaults={
            'display_name': 'Group Member',
            'description': 'Regular meeting member',
            'is_active': True,
            'term_months': 0,
            'can_manage_users': False,
            'module_permissions': {},
            'show_on_public_site': False,
            'warn_on_multiple_holders': False,
            'order': 100,  # Show last in lists
        }
    )


def remove_group_member(apps, schema_editor):
    ServicePosition = apps.get_model('core', 'ServicePosition')
    ServicePosition.objects.filter(name='group_member').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_public_officers_display'),
    ]

    operations = [
        migrations.RunPython(create_group_member, remove_group_member),
    ]
