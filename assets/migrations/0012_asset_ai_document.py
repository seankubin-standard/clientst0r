from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0011_asset_profile_document'),
        ('docs', '0012_add_system_package_scan'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='ai_document',
            field=models.ForeignKey(
                blank=True,
                help_text='AI-generated documentation for this asset',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='ai_doc_assets',
                to='docs.document',
            ),
        ),
    ]
