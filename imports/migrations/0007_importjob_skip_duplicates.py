from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imports', '0006_csv_import_mapper'),
    ]

    operations = [
        migrations.AddField(
            model_name='importjob',
            name='skip_duplicates',
            field=models.BooleanField(
                default=True,
                help_text='Skip items already imported in any previous completed job for this organization',
            ),
        ),
    ]
