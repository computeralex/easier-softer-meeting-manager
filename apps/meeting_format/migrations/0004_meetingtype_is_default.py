"""
Add MeetingType.is_default and backfill existing data so each meeting has
exactly one default meeting type (the earliest-created by order/pk).
"""
from django.db import migrations, models


def seed_default_per_meeting(apps, schema_editor):
    MeetingType = apps.get_model("meeting_format", "MeetingType")
    # Group by meeting; flag the earliest (by order, then pk) as default
    # unless a default is already set.
    seen = set()
    for mt in MeetingType.objects.order_by("meeting_id", "order", "pk"):
        if mt.meeting_id in seen:
            continue
        seen.add(mt.meeting_id)
        if not mt.is_default:
            mt.is_default = True
            mt.save(update_fields=["is_default"])


def noop_reverse(apps, schema_editor):
    # Nothing to undo — the column will be dropped when the schema migration
    # reverses.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("meeting_format", "0003_remove_blockvariation_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="meetingtype",
            name="is_default",
            field=models.BooleanField(
                default=False,
                help_text="Used when no specific type is selected for the meeting.",
            ),
        ),
        migrations.RunPython(seed_default_per_meeting, noop_reverse),
    ]
