from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0019_add_psa_ticket_and_alerts'),
    ]

    operations = [
        migrations.AddField(
            model_name='unificonnection',
            name='site_org_map',
            field=models.JSONField(blank=True, default=dict, help_text='Cloud mode: maps site name to organization ID'),
        ),
    ]
