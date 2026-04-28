"""
Cron-driven runner for PSA recurring ticket schedules.

Wire to a systemd timer or crontab — runs every 15 minutes is a sane
default. Idempotent: each run only acts on schedules whose next_run_at
is in the past, then rolls next_run_at forward by one frequency
interval. If a schedule fires while the runner is paused, it catches
up on the next run (one ticket per overdue cycle, capped at 50 to
prevent runaway).
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from psa.models import (
    RecurringTicketSchedule, Ticket, TicketStatus,
)


class Command(BaseCommand):
    help = 'Create tickets from active RecurringTicketSchedule rows whose next_run_at has passed.'

    def add_arguments(self, parser):
        parser.add_argument('--max-per-schedule', type=int, default=50,
                            help='Cap on catch-up ticket creation per schedule.')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        cap = options['max_per_schedule']
        dry = options['dry_run']
        now = timezone.now()
        qs = RecurringTicketSchedule.objects.filter(is_active=True, next_run_at__lte=now)

        new_status = TicketStatus.objects.filter(slug='new').first()
        if new_status is None:
            self.stdout.write(self.style.ERROR('No "new" TicketStatus — run psa_seed_defaults first.'))
            return

        created = 0
        for sched in qs.select_related('queue', 'priority', 'ticket_type', 'assigned_to'):
            cycles = 0
            while sched.next_run_at <= now and cycles < cap:
                if dry:
                    self.stdout.write(f'[dry] would create ticket from "{sched.name}" at {sched.next_run_at.isoformat()}')
                else:
                    try:
                        Ticket.objects.create(
                            organization=sched.organization,
                            subject=sched.template_subject,
                            description=sched.template_body,
                            queue=sched.queue,
                            priority=sched.priority,
                            ticket_type=sched.ticket_type,
                            status=new_status,
                            assigned_to=sched.assigned_to,
                            source='recurring',
                            recurring_schedule=sched,
                        )
                        created += 1
                    except Exception as exc:
                        sched.last_error = str(exc)[:1000]
                        sched.save(update_fields=['last_error'])
                        self.stdout.write(self.style.ERROR(
                            f'{sched.name}: {exc}'
                        ))
                        break
                sched.advance_next_run()
                cycles += 1

            if not dry:
                sched.last_run_at = now
                sched.last_error = ''
                sched.save(update_fields=['next_run_at', 'last_run_at', 'last_error'])

        self.stdout.write(self.style.SUCCESS(
            f'{"[dry] " if dry else ""}Created {created} ticket(s) from {qs.count()} due schedule(s).'
        ))
