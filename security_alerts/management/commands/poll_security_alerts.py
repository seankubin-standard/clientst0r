"""
Run every 5 minutes via cron. For each active SecurityVendorConnection
whose poll_interval has elapsed, look up the matching SecurityProvider
adapter and run sync().
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Poll all active security-vendor connections for new alerts.'

    def add_arguments(self, parser):
        parser.add_argument('--connection-id', type=int)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        from security_alerts.models import SecurityVendorConnection
        from integrations.sdk.registry import get as get_provider

        qs = SecurityVendorConnection.objects.filter(is_active=True, sync_enabled=True)
        if opts['connection_id']:
            qs = qs.filter(pk=opts['connection_id'])

        now = timezone.now()
        ran = 0
        for conn in qs:
            # Skip if last_sync_at is recent enough
            if conn.last_sync_at:
                next_due = conn.last_sync_at + timedelta(minutes=conn.poll_interval_minutes)
                if next_due > now:
                    continue
            adapter_slug = f'security_{conn.provider}'
            # Adapter slug is 'security_<provider>' — look up by full slug first,
            # then fall back to provider-only.
            adapter = get_provider(adapter_slug) or get_provider(conn.provider)
            if not adapter:
                self.stdout.write(f'  [skip] No adapter registered for {conn.provider}')
                continue
            self.stdout.write(f'  Polling {conn.name}...')
            if opts['dry_run']:
                continue
            result = adapter.sync(conn)
            self.stdout.write(f'    -> {result}')
            ran += 1

        self.stdout.write(self.style.SUCCESS(f'Polled {ran} connection{"s" if ran != 1 else ""}.'))
