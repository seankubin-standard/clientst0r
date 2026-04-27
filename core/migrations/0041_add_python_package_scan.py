from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_vault_password_expiry_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='PythonPackageScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scan_date', models.DateTimeField(auto_now_add=True)),
                ('total_packages', models.IntegerField(default=0)),
                ('vulnerable_packages', models.IntegerField(default=0, help_text='Distinct packages with at least one vuln')),
                ('total_vulnerabilities', models.IntegerField(default=0, help_text='Total vuln findings (a package can have multiple)')),
                ('critical_count', models.IntegerField(default=0)),
                ('high_count', models.IntegerField(default=0)),
                ('medium_count', models.IntegerField(default=0)),
                ('low_count', models.IntegerField(default=0)),
                ('unknown_count', models.IntegerField(default=0)),
                ('scan_succeeded', models.BooleanField(default=True)),
                ('scan_error', models.TextField(blank=True)),
                ('scan_data', models.JSONField(default=dict, help_text='Full pip-audit results: list of {name, version, vulns: [{id, fix_versions, severity, summary}]}')),
            ],
            options={
                'db_table': 'python_package_scans',
                'ordering': ['-scan_date'],
                'indexes': [models.Index(fields=['-scan_date'], name='python_pack_scan_da_idx')],
            },
        ),
    ]
