"""
No-op migration stub.

This migration previously added the `mode` field to UnifiConnection but that
operation was already performed by 0016_unifi_cloud_mode.py.  This file exists
only so that any server-side 0017_merge_* migration that lists
('integrations', '0016_unificonnection_mode') as a dependency can still resolve.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0016_unifi_cloud_mode'),
    ]

    operations = []
