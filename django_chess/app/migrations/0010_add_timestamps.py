# Generated manually

from django.db import migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_update_game_names_with_uuid_seed'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),  # type: ignore[no-untyped-call]
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),  # type: ignore[no-untyped-call]
            preserve_default=False,
        ),
    ]
