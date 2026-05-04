"""
Phase 13 v7 (v3.17.266): cron-driven runner for RecurringPurchaseTemplate.

Wire to a daily systemd timer. Idempotent — each run only acts on
templates whose next_run_at is in the past, spawns a draft PR, and
rolls next_run_at forward by one cycle. Disabled templates are skipped.
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from psa.models import RecurringPurchaseTemplate


class Command(BaseCommand):
    help = 'Spawn draft PRs from RecurringPurchaseTemplate rows whose next_run_at has passed.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be spawned without creating PRs.')
        parser.add_argument('--max-per-template', type=int, default=12,
                            help='Cap catch-up cycles per template (in case the cron was paused).')

    def handle(self, *args, **options):
        dry = options['dry_run']
        cap = options['max_per_template']
        today = date.today()
        qs = RecurringPurchaseTemplate.objects.filter(
            enabled=True, next_run_at__lte=today,
        )

        spawned = 0
        for tpl in qs:
            cycles = 0
            while tpl.next_run_at <= today and cycles < cap:
                if dry:
                    self.stdout.write(
                        f'[dry] would spawn PR from "{tpl.name}" '
                        f'(next_run_at={tpl.next_run_at}, recurrence={tpl.recurrence})'
                    )
                    # In dry run, advance next_run_at locally so the
                    # while-loop exits — but don't persist.
                    tpl.next_run_at = RecurringPurchaseTemplate._advance(
                        tpl.next_run_at, tpl.recurrence,
                    )
                else:
                    try:
                        pr = tpl.spawn_pr()
                        spawned += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'Spawned {pr.pr_number} from "{tpl.name}" '
                            f'(next_run_at now={tpl.next_run_at})'
                        ))
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(
                            f'{tpl.name}: {exc}'
                        ))
                        break
                cycles += 1

        self.stdout.write(self.style.SUCCESS(
            f'{"[dry] " if dry else ""}Processed {qs.count()} template(s); '
            f'{spawned} PR(s) created.'
        ))
