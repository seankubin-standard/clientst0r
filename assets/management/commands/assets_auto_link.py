"""
Phase 16 v6 (v3.17.301): heuristic asset auto-linker.

Scans assets within an organization for obvious relationships and
creates `Relationship` rows when missing. The heuristics are
conservative on purpose — false positives create noise in the
relationship map.

Heuristics shipped today:
  1. **Same /24 subnet** — assets sharing the first three octets get a
     `related` relationship (so a relationship-map query from any one
     surfaces the others on the same network segment).
  2. **Gateway-of-segment** — if exactly one asset on a /24 segment is
     `asset_type` in (`firewall`, `router`, `gateway`), other assets on
     that segment get a `depends` relationship pointing at it (since
     they go offline if the gateway does).

Idempotent: skips relationships that already exist (the model has a
unique_together so duplicates would raise).
"""
from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from assets.models import Asset, Relationship
from core.models import Organization


GATEWAY_TYPES = {'firewall', 'router', 'gateway'}


class Command(BaseCommand):
    help = 'Heuristically link assets within each org by IP subnet.'

    def add_arguments(self, parser):
        parser.add_argument('--organization', type=str, default=None,
                            help='Limit to one org by slug.')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry = options['dry_run']
        slug = options.get('organization')

        orgs = Organization.objects.filter(is_active=True)
        if slug:
            orgs = orgs.filter(slug=slug)

        related_count = 0
        depends_count = 0

        for org in orgs:
            # Use Python-side filter to dodge any quirky interaction
            # between the IP field's NULL representation and Django
            # exclude/isnull lookups across drivers (sqlite vs MariaDB).
            all_assets = Asset.objects.filter(organization=org)
            assets = [a for a in all_assets if a.ip_address]
            if not assets:
                continue

            # Bucket by /24 prefix (first 3 octets)
            buckets = defaultdict(list)
            for a in assets:
                if not a.ip_address or ':' in str(a.ip_address):
                    continue  # IPv6 not handled in this pass
                parts = str(a.ip_address).split('.')
                if len(parts) != 4:
                    continue
                prefix = '.'.join(parts[:3])
                buckets[prefix].append(a)

            for prefix, members in buckets.items():
                if len(members) < 2:
                    continue
                gateways = [a for a in members if a.asset_type in GATEWAY_TYPES]
                gateway = gateways[0] if len(gateways) == 1 else None

                # Pairwise `related` between non-gateway members
                non_gw = [a for a in members if a is not gateway] if gateway else members
                for i, a in enumerate(non_gw):
                    for b in non_gw[i + 1:]:
                        if dry:
                            self.stdout.write(
                                f'[dry] org={org.slug} '
                                f'related: {a.name} ↔ {b.name} (subnet {prefix})'
                            )
                            continue
                        try:
                            Relationship.objects.get_or_create(
                                organization=org,
                                source_type='asset', source_id=a.pk,
                                target_type='asset', target_id=b.pk,
                                relation_type='related',
                            )
                            related_count += 1
                        except IntegrityError:
                            pass

                # Gateway gets `depends` from each other asset
                if gateway is not None:
                    for a in non_gw:
                        if dry:
                            self.stdout.write(
                                f'[dry] org={org.slug} '
                                f'depends: {a.name} → {gateway.name}'
                            )
                            continue
                        try:
                            Relationship.objects.get_or_create(
                                organization=org,
                                source_type='asset', source_id=a.pk,
                                target_type='asset', target_id=gateway.pk,
                                relation_type='depends',
                            )
                            depends_count += 1
                        except IntegrityError:
                            pass

        self.stdout.write(self.style.SUCCESS(
            f'{"[dry] " if dry else ""}Created {related_count} related, '
            f'{depends_count} depends rows.'
        ))
