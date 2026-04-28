"""
Seed default PSA reference data: queues, statuses, priorities, ticket types.

Idempotent — safe to run repeatedly. Uses get_or_create so existing
operator-customised rows are preserved.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from psa.models import Queue, TicketPriority, TicketStatus, TicketType


QUEUES = [
    'Helpdesk',
    'Escalations',
    'Projects',
    'Security',
    'Monitoring',
    'Procurement',
    'Client Success',
]

# (name, is_terminal, pauses_sla)
STATUSES = [
    ('New', False, False),
    ('Assigned', False, False),
    ('In Progress', False, False),
    ('Waiting on Client', False, True),
    ('Waiting on Vendor', False, True),
    ('Scheduled', False, False),
    ('Escalated', False, False),
    ('Resolved', True, False),
    ('Closed', True, False),
    ('Cancelled', True, False),
]

# (code, name, description, response_minutes, resolution_minutes)
# Defaults match the spec; admins can edit per-priority targets.
PRIORITIES = [
    ('P1', 'Critical', 'Production down or imminent business impact.', 15, 240),
    ('P2', 'High',     'Significant impact, workaround partially available.', 30, 480),
    ('P3', 'Normal',   'Single-user impact or routine issue.', 240, 4320),
    ('P4', 'Low',      'Minor issue, low impact.', 1440, 7200),
    ('P5', 'Informational', 'No service impact, informational only.', 2880, 14400),
]

TYPES = [
    'Incident',
    'Service Request',
    'Change Request',
    'Problem',
    'Project Task',
    'Security Event',
    'Monitoring Alert',
    'Onboarding',
    'Offboarding',
    'Procurement',
    'Documentation Request',
    'Access Request',
    'Vendor Escalation',
    'Calendar Dispatch',
]


class Command(BaseCommand):
    help = 'Seed default PSA queues, statuses, priorities, and ticket types'

    def handle(self, *args, **opts):
        created_total = 0
        existing_total = 0

        # Queues
        for i, name in enumerate(QUEUES):
            _, created = Queue.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name), 'sort_order': i, 'is_active': True},
            )
            created_total += 1 if created else 0
            existing_total += 0 if created else 1

        # Statuses
        for i, (name, is_terminal, pauses_sla) in enumerate(STATUSES):
            _, created = TicketStatus.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slugify(name),
                    'is_terminal': is_terminal,
                    'pauses_sla': pauses_sla,
                    'sort_order': i,
                },
            )
            created_total += 1 if created else 0
            existing_total += 0 if created else 1

        # Priorities
        for i, (code, name, desc, resp, res) in enumerate(PRIORITIES):
            _, created = TicketPriority.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': desc,
                    'response_target_minutes': resp,
                    'resolution_target_minutes': res,
                    'sort_order': i,
                },
            )
            created_total += 1 if created else 0
            existing_total += 0 if created else 1

        # Ticket types
        for i, name in enumerate(TYPES):
            _, created = TicketType.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name), 'sort_order': i, 'is_active': True},
            )
            created_total += 1 if created else 0
            existing_total += 0 if created else 1

        self.stdout.write(self.style.SUCCESS(
            f'PSA seed complete — {created_total} created, {existing_total} already existed.'
        ))
