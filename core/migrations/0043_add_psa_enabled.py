from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_add_system_warning_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsetting',
            name='psa_enabled',
            field=models.BooleanField(default=False, help_text='Enable native PSA / Service Desk feature (off by default)'),
        ),
    ]
