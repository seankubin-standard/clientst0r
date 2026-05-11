from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0060_organization_exposure_score_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BetaTesterRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('google_account_email', models.EmailField(
                    help_text='The Gmail address signed into Play Store on the device that will install the beta.',
                    max_length=254,
                )),
                ('company', models.CharField(blank=True, max_length=200)),
                ('role', models.CharField(blank=True, max_length=200)),
                ('message', models.TextField(blank=True)),
                ('heard_from', models.CharField(blank=True, max_length=200)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending review'),
                        ('approved', 'Approved (give me the URL)'),
                        ('added_to_play', 'Added to Play Console'),
                        ('rejected', 'Rejected'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('decision_note', models.CharField(blank=True, max_length=500)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('decided_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='beta_tester_decisions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'core_beta_tester_requests',
                'ordering': ['-submitted_at'],
                'indexes': [
                    models.Index(fields=['status', '-submitted_at'], name='core_beta_t_status_idx'),
                    models.Index(fields=['google_account_email'], name='core_beta_t_email_idx'),
                ],
            },
        ),
    ]
