"""
No-op migration stub.

This migration previously added the `mode` field to UnifiConnection but that
operation was already performed by 0016_unifi_cloud_mode.py.  This file exists
only so that any server-side 0017_merge_* migration that lists
('integrations', '0016_unificonnection_mode') as a dependency can still resolve.

Both 0016_unifi_cloud_mode and 0016_unificonnection_mode are independent
branches off 0015_m365connection.  Declaring the dependency on 0016_unifi_cloud_mode
(as the previous stub did) caused InconsistentMigrationHistory on servers where
the two 0016 migrations were applied in the opposite order.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0015_m365connection'),
    ]

    operations = []
