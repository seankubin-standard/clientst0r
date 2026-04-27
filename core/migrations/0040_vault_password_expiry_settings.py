from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_asset_health_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsetting',
            name='notify_on_password_expiry',
            field=models.BooleanField(default=True, help_text='Send vault password expiration warnings'),
        ),
        migrations.AddField(
            model_name='systemsetting',
            name='password_expiry_warning_days',
            field=models.PositiveIntegerField(default=14, help_text='Days before vault password expiry to warn'),
        ),
    ]
