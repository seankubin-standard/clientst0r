# Safe manual migration: avoids RemoveIndex/RenameIndex crashing on MySQL
# when the index may already be in the target state from migration 0011.

from django.db import migrations


def remove_lat_lon_idx_if_exists(apps, schema_editor):
    db = schema_editor.connection.vendor
    if db == 'mysql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.STATISTICS
                WHERE table_schema = DATABASE()
                  AND table_name = 'rmm_devices'
                  AND index_name = 'rmm_devices_lat_lon_idx'
            """)
            if cursor.fetchone()[0]:
                cursor.execute("ALTER TABLE rmm_devices DROP INDEX rmm_devices_lat_lon_idx")
    else:
        schema_editor.execute("DROP INDEX IF EXISTS rmm_devices_lat_lon_idx")


def rename_ext_obj_map_idx_if_needed(apps, schema_editor):
    db = schema_editor.connection.vendor
    if db == 'mysql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.STATISTICS
                WHERE table_schema = DATABASE()
                  AND table_name = 'integrations_externalobjectmap'
                  AND index_name = 'ext_obj_map_conn_idx'
            """)
            old_exists = cursor.fetchone()[0]
            if old_exists:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.STATISTICS
                    WHERE table_schema = DATABASE()
                      AND table_name = 'integrations_externalobjectmap'
                      AND index_name = 'external_ob_connect_9c6dfd_idx'
                """)
                new_exists = cursor.fetchone()[0]
                if not new_exists:
                    cursor.execute(
                        "ALTER TABLE integrations_externalobjectmap "
                        "RENAME INDEX ext_obj_map_conn_idx TO external_ob_connect_9c6dfd_idx"
                    )
    # sqlite/postgres: no-op (0011 already handled or indexes don't exist)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0011_sync_index_state'),
    ]

    operations = [
        migrations.RunPython(remove_lat_lon_idx_if_exists, noop),
        migrations.RunPython(rename_ext_obj_map_idx_if_needed, noop),
    ]
