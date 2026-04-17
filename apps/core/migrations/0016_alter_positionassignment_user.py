"""
Pin PositionAssignment.user FK to core.User explicitly.

Migration 0005 created this FK with `to=settings.AUTH_USER_MODEL`, which is
evaluated at migrate time. In the SaaS wrapper, AUTH_USER_MODEL resolves to
saas_accounts.User (public schema), so the DB constraint ends up pointing at
public.saas_accounts_user. But the runtime model declares the FK as local to
core.User (`to='User'`), and the form's user queryset returns core.User
instances. Writing a core.User.pk into a column constrained to saas_accounts
fails the FK check → 500 on `/dashboard/positions/<id>/assign/`.

Pinning to `core.User` aligns the DB constraint with the model and keeps the
relationship tenant-local. In standalone deployments (AUTH_USER_MODEL =
core.User), this AlterField is a no-op — migration state already matches.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_allow_placeholder_users"),
    ]

    operations = [
        migrations.AlterField(
            model_name="positionassignment",
            name="user",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="position_assignments",
                to="core.User",
            ),
        ),
    ]
