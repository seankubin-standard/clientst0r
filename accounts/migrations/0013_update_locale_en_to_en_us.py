"""
Data migration: Update locale 'en' -> 'en-us' for existing UserProfile rows,
and extend the max_length to 10 to accommodate 'en-us' and 'pt-br'.
"""
from django.db import migrations, models


def migrate_locale_en_to_en_us(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.filter(locale='en').update(locale='en-us')


def reverse_locale_en_us_to_en(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.filter(locale='en-us').update(locale='en')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_add_time_format'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='locale',
            field=models.CharField(
                max_length=10,
                default='en-us',
                choices=[
                    ('en-us', 'English (US)'),
                    ('es',    'Spanish'),
                    ('fr',    'French'),
                    ('de',    'German'),
                    ('pt-br', 'Portuguese (Brazil)'),
                ],
            ),
        ),
        migrations.RunPython(
            migrate_locale_en_to_en_us,
            reverse_code=reverse_locale_en_us_to_en,
        ),
    ]
