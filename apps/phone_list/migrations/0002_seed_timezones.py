"""
Seed default time zones.
"""
from django.db import migrations


def seed_timezones(apps, schema_editor):
    TimeZone = apps.get_model('phone_list', 'TimeZone')
    timezones = [
        {'code': 'EST', 'display_name': 'Eastern', 'order': 1},
        {'code': 'CST', 'display_name': 'Central', 'order': 2},
        {'code': 'MST', 'display_name': 'Mountain', 'order': 3},
        {'code': 'PST', 'display_name': 'Pacific', 'order': 4},
    ]
    for tz in timezones:
        TimeZone.objects.get_or_create(code=tz['code'], defaults=tz)


def reverse_seed(apps, schema_editor):
    TimeZone = apps.get_model('phone_list', 'TimeZone')
    TimeZone.objects.filter(code__in=['EST', 'CST', 'MST', 'PST']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('phone_list', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_timezones, reverse_seed),
    ]
