"""
Management command to auto-sync network device connections and import assets.

Run via cron:
    */30 * * * * /home/administrator/venv/bin/python manage.py sync_network_assets

Or schedule via Settings > General.

Only syncs connections where auto_sync_assets=True and enough time has passed
since last_asset_sync_at (based on sync_interval_minutes).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Auto-sync network device connections and import to asset registry'

    def handle(self, *args, **options):
        from integrations.models import UnifiConnection, OmadaConnection, GrandstreamConnection
        from integrations.views import _import_devices_to_assets

        now = timezone.now()
        synced = 0
        errors = 0

        # ----------------------------------------------------------------
        # UniFi connections
        # ----------------------------------------------------------------
        for conn in UnifiConnection.objects.filter(is_active=True, auto_sync_assets=True):
            if not self._should_sync(conn, now):
                continue
            try:
                from integrations.views import _get_unifi_provider
                provider = _get_unifi_provider(conn)
                data = provider.sync()
                conn.cached_data = data
                conn.last_sync_at = now
                conn.last_sync_status = 'ok'
                conn.last_error = ''

                all_devices = []
                for s in data.get('sites', []):
                    for d in s.get('devices', []):
                        from django.core.validators import validate_ipv46_address

                        def _clean_ip(raw):
                            try:
                                validate_ipv46_address(str(raw))
                                return str(raw)
                            except Exception:
                                return ''

                        mac = (d.get('mac') or d.get('macAddress') or '').lower().replace('-', ':')
                        all_devices.append({
                            'name': d.get('name') or d.get('hostname') or mac or 'Unknown Device',
                            'mac': mac,
                            'ip': _clean_ip(d.get('ip') or d.get('ipAddress') or ''),
                            'model': d.get('model') or d.get('shortname') or '',
                            'asset_type': 'wireless_ap',
                            'manufacturer': 'Ubiquiti',
                            'serial_number': d.get('serial') or d.get('serialNumber') or d.get('serialno') or '',
                            'os_version': d.get('version') or d.get('firmwareVersion') or '',
                        })

                result = _import_devices_to_assets(conn.organization, all_devices, 'UniFi')
                conn.last_asset_sync_at = now
                conn.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[UniFi] {conn.name}: synced, imported "
                        f"{result['created']} new / {result['updated']} updated / {result['skipped']} unchanged"
                    )
                )
                synced += 1
            except Exception as e:
                conn.last_sync_status = 'error'
                conn.last_error = str(e)
                conn.save(update_fields=['last_sync_status', 'last_error'])
                self.stderr.write(self.style.ERROR(f"[UniFi] {conn.name}: ERROR — {e}"))
                logger.error(f"sync_network_assets UniFi {conn.name}: {e}", exc_info=True)
                errors += 1

        # ----------------------------------------------------------------
        # Omada connections
        # ----------------------------------------------------------------
        for conn in OmadaConnection.objects.filter(is_active=True, auto_sync_assets=True):
            if not self._should_sync(conn, now):
                continue
            try:
                from integrations.providers.omada import OmadaProvider
                creds = conn.get_credentials()
                provider = OmadaProvider(
                    host=conn.host,
                    username=creds.get('username', ''),
                    password=creds.get('password', ''),
                    verify_ssl=conn.verify_ssl,
                )
                data = provider.sync()
                conn.cached_data = data
                conn.last_sync_at = now
                conn.last_sync_status = 'ok'
                conn.last_error = ''

                all_devices = []
                for s in data.get('sites', []):
                    all_devices.extend(s.get('devices', []))

                result = _import_devices_to_assets(conn.organization, all_devices, 'Omada')
                conn.last_asset_sync_at = now
                conn.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[Omada] {conn.name}: synced, imported "
                        f"{result['created']} new / {result['updated']} updated / {result['skipped']} unchanged"
                    )
                )
                synced += 1
            except Exception as e:
                conn.last_sync_status = 'error'
                conn.last_error = str(e)
                conn.save(update_fields=['last_sync_status', 'last_error'])
                self.stderr.write(self.style.ERROR(f"[Omada] {conn.name}: ERROR — {e}"))
                logger.error(f"sync_network_assets Omada {conn.name}: {e}", exc_info=True)
                errors += 1

        # ----------------------------------------------------------------
        # Grandstream connections
        # ----------------------------------------------------------------
        for conn in GrandstreamConnection.objects.filter(is_active=True, auto_sync_assets=True):
            if not self._should_sync(conn, now):
                continue
            try:
                from integrations.providers.grandstream import GrandstreamProvider
                creds = conn.get_credentials()
                provider = GrandstreamProvider(
                    host=conn.host,
                    api_key=creds.get('api_key', ''),
                    verify_ssl=conn.verify_ssl,
                )
                data = provider.sync()
                conn.cached_data = data
                conn.last_sync_at = now
                conn.last_sync_status = 'ok'
                conn.last_error = ''

                all_devices = []
                for s in data.get('sites', []):
                    all_devices.extend(s.get('devices', []))

                result = _import_devices_to_assets(conn.organization, all_devices, 'Grandstream')
                conn.last_asset_sync_at = now
                conn.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[Grandstream] {conn.name}: synced, imported "
                        f"{result['created']} new / {result['updated']} updated / {result['skipped']} unchanged"
                    )
                )
                synced += 1
            except Exception as e:
                conn.last_sync_status = 'error'
                conn.last_error = str(e)
                conn.save(update_fields=['last_sync_status', 'last_error'])
                self.stderr.write(self.style.ERROR(f"[Grandstream] {conn.name}: ERROR — {e}"))
                logger.error(f"sync_network_assets Grandstream {conn.name}: {e}", exc_info=True)
                errors += 1

        self.stdout.write(f"\nDone. {synced} synced, {errors} error(s).")

    def _should_sync(self, conn, now):
        """Return True if this connection is due for a sync."""
        interval = getattr(conn, 'sync_interval_minutes', 720)
        if interval == 0:
            return False
        last = getattr(conn, 'last_asset_sync_at', None)
        if last is None:
            return True
        return (now - last) >= timedelta(minutes=interval)
