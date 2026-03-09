from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0014_unificonnection'),
        ('docs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='M365Connection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='Friendly name for this connection', max_length=255)),
                ('tenant_id', models.CharField(help_text='Azure AD tenant ID (Directory ID)', max_length=255)),
                ('encrypted_credentials', models.TextField(blank=True, help_text='Encrypted JSON with client_id and client_secret')),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_sync_status', models.CharField(blank=True, max_length=50)),
                ('last_error', models.TextField(blank=True)),
                ('cached_data', models.JSONField(blank=True, default=dict)),
                ('doc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='m365_connections', to='docs.document')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='m365_connections', to='core.organization')),
            ],
            options={
                'db_table': 'm365_connections',
                'ordering': ['name'],
                'unique_together': {('organization', 'name')},
            },
        ),
    ]
