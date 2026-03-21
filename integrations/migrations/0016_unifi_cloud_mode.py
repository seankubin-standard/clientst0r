from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0015_m365connection'),
    ]

    operations = [
        migrations.AddField(
            model_name='unificonnection',
            name='mode',
            field=models.CharField(
                choices=[
                    ('self_hosted', 'Self-hosted (local controller)'),
                    ('cloud', 'Cloud (UniFi Site Manager / ui.com)'),
                ],
                default='self_hosted',
                help_text='Self-hosted controller or UniFi Site Manager cloud API',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='unificonnection',
            name='host',
            field=models.URLField(
                blank=True,
                help_text='UniFi controller URL (self-hosted only), e.g. https://192.168.1.1',
                max_length=500,
            ),
        ),
    ]
