from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0013_remove_rmmdevice_rmm_devices_lat_lon_idx_and_more'),
        ('docs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnifiConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='Friendly name for this connection', max_length=255)),
                ('host', models.URLField(help_text='UniFi controller URL, e.g. https://192.168.1.1', max_length=500)),
                ('verify_ssl', models.BooleanField(default=False, help_text='Verify SSL certificate (disable for self-signed)')),
                ('encrypted_credentials', models.TextField(blank=True, help_text='Encrypted JSON with api_key')),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_sync_status', models.CharField(blank=True, max_length=50)),
                ('last_error', models.TextField(blank=True)),
                ('cached_data', models.JSONField(blank=True, default=dict)),
                ('doc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unifi_connections', to='docs.document')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unifi_connections', to='core.organization')),
            ],
            options={
                'db_table': 'unifi_connections',
                'ordering': ['name'],
                'unique_together': {('organization', 'name')},
            },
        ),
    ]
