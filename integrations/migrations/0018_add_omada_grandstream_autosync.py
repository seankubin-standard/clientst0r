"""
Migration: add auto-sync fields to UnifiConnection, create OmadaConnection
and GrandstreamConnection tables.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0017_merge_0016_unifi_cloud_mode_0016_unificonnection_mode'),
        ('core', '0001_initial'),
    ]

    operations = [
        # ----------------------------------------------------------------
        # Add auto-sync fields to UnifiConnection
        # ----------------------------------------------------------------
        migrations.AddField(
            model_name='unificonnection',
            name='auto_sync_assets',
            field=models.BooleanField(
                default=False,
                help_text='Automatically import devices to asset registry on each sync',
            ),
        ),
        migrations.AddField(
            model_name='unificonnection',
            name='sync_interval_minutes',
            field=models.PositiveIntegerField(
                default=720,
                help_text='Auto-sync interval in minutes (0=disabled)',
            ),
        ),
        migrations.AddField(
            model_name='unificonnection',
            name='last_asset_sync_at',
            field=models.DateTimeField(null=True, blank=True),
        ),

        # ----------------------------------------------------------------
        # OmadaConnection table
        # ----------------------------------------------------------------
        migrations.CreateModel(
            name='OmadaConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('host', models.URLField(help_text='Omada controller URL, e.g. https://192.168.1.1:8043')),
                ('verify_ssl', models.BooleanField(default=False)),
                ('encrypted_credentials', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_sync_status', models.CharField(blank=True, max_length=20)),
                ('last_error', models.TextField(blank=True)),
                ('cached_data', models.JSONField(blank=True, default=dict)),
                ('auto_sync_assets', models.BooleanField(
                    default=False,
                    help_text='Automatically import devices to asset registry on each sync',
                )),
                ('sync_interval_minutes', models.PositiveIntegerField(
                    default=720,
                    help_text='Auto-sync interval in minutes (0=disabled)',
                )),
                ('last_asset_sync_at', models.DateTimeField(blank=True, null=True)),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='omada_connections',
                    to='core.organization',
                )),
            ],
            options={
                'db_table': 'omada_connections',
                'ordering': ['name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='omadaconnection',
            unique_together={('organization', 'name')},
        ),

        # ----------------------------------------------------------------
        # GrandstreamConnection table
        # ----------------------------------------------------------------
        migrations.CreateModel(
            name='GrandstreamConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('host', models.URLField(
                    default='https://gwn.cloud',
                    help_text='GWN Manager URL, e.g. https://gwn.cloud or self-hosted URL',
                )),
                ('verify_ssl', models.BooleanField(default=False)),
                ('encrypted_credentials', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_sync_status', models.CharField(blank=True, max_length=20)),
                ('last_error', models.TextField(blank=True)),
                ('cached_data', models.JSONField(blank=True, default=dict)),
                ('auto_sync_assets', models.BooleanField(
                    default=False,
                    help_text='Automatically import devices to asset registry on each sync',
                )),
                ('sync_interval_minutes', models.PositiveIntegerField(
                    default=720,
                    help_text='Auto-sync interval in minutes (0=disabled)',
                )),
                ('last_asset_sync_at', models.DateTimeField(blank=True, null=True)),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='grandstream_connections',
                    to='core.organization',
                )),
            ],
            options={
                'db_table': 'grandstream_connections',
                'ordering': ['name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='grandstreamconnection',
            unique_together={('organization', 'name')},
        ),
    ]
