from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_add_python_package_scan'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemWarningNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('warning_id', models.CharField(help_text='Stable warning id from system_warnings.collect_system_warnings()', max_length=200, unique=True)),
                ('severity', models.CharField(max_length=20)),
                ('title', models.TextField()),
                ('notified_at', models.DateTimeField(auto_now_add=True)),
                ('recipients_count', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'system_warning_notifications',
                'ordering': ['-notified_at'],
                'indexes': [models.Index(fields=['-notified_at'], name='system_warn_notifie_idx')],
            },
        ),
    ]
