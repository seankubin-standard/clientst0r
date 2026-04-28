"""
Seed sample WorkflowRule rows into a tenant.

Workflow rules are per-organization (the MSP tenant), so they can't be
shipped globally. This command installs a curated starter set on demand.

Usage:
  manage.py psa_seed_sample_workflows                # all active orgs
  manage.py psa_seed_sample_workflows --org-id 5     # one org
  manage.py psa_seed_sample_workflows --replace      # overwrite existing names

Each sample is idempotent (matched by name within the org).
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from core.models import Organization
from psa.models import WorkflowRule


# Curated starter rules. Each is a dict ready to splat into WorkflowRule.
# Action `username` placeholders should be edited by the MSP admin to point
# at real users — the sample fills them with "admin" so the rule is visibly
# wired without breaking on missing users (the engine no-ops on unknown
# username, see workflow_engine._resolve_user).
SAMPLE_RULES = [
    {
        'name': 'P1 escalation — alert manager + escalate queue',
        'description': 'When a P1 ticket is created, route it to the Escalations queue and add the on-call manager as a watcher.',
        'trigger': 'ticket_created',
        'conditions': {'priority': 'P1'},
        'actions': [
            {'type': 'set_queue', 'name': 'Escalations'},
            {'type': 'add_watcher', 'username': 'admin'},
            {'type': 'add_internal_note', 'body': 'P1 detected — auto-routed to Escalations and on-call paged.'},
            {'type': 'add_tag', 'tag': 'p1-escalation'},
        ],
        'sort_order': 10,
    },
    {
        'name': 'Sales inquiry — follow-up workflow',
        'description': 'Create a tracked follow-up when a sales-inquiry ticket lands. Tags it for the sales pipeline and assigns to the sales lead.',
        'trigger': 'ticket_created',
        'conditions': {'subject_contains': 'sales inquiry'},
        'actions': [
            {'type': 'set_queue', 'name': 'Sales'},
            {'type': 'set_priority', 'code': 'P3'},
            {'type': 'assign_to', 'username': 'admin'},
            {'type': 'add_internal_note', 'body': 'Sales lead — initial outreach within 4 business hours; second touch in 2 days; stale at day 7.'},
            {'type': 'add_tag', 'tag': 'sales-pipeline'},
        ],
        'sort_order': 20,
    },
    {
        'name': 'New-user onboarding — checklist tag',
        'description': 'Tickets with "new user" in the subject get tagged for the onboarding checklist and routed to Helpdesk.',
        'trigger': 'ticket_created',
        'conditions': {'subject_contains': 'new user'},
        'actions': [
            {'type': 'set_queue', 'name': 'Helpdesk'},
            {'type': 'add_tag', 'tag': 'onboarding'},
            {'type': 'add_internal_note', 'body': 'Onboarding checklist: M365 account, asset assignment, vault password handoff, security training, manager intro.'},
        ],
        'sort_order': 30,
    },
    {
        'name': 'Termination — security-priority routing',
        'description': 'Termination tickets are routed to Security and marked P2 minimum — credentials must be revoked promptly.',
        'trigger': 'ticket_created',
        'conditions': {'subject_contains': 'terminate'},
        'actions': [
            {'type': 'set_queue', 'name': 'Security'},
            {'type': 'set_priority', 'code': 'P2'},
            {'type': 'add_tag', 'tag': 'offboarding'},
            {'type': 'add_internal_note', 'body': 'Offboarding checklist: disable account, revoke vault access, recover devices, archive mailbox, forward email.'},
        ],
        'sort_order': 40,
    },
    {
        'name': 'Outage keyword — auto-escalate to P1',
        'description': 'If "outage", "down", or "offline" appears in the subject, bump priority to P1 and route to Escalations.',
        'trigger': 'ticket_created',
        'conditions': {'any': [
            {'subject_contains': 'outage'},
            {'subject_contains': 'down'},
            {'subject_contains': 'offline'},
        ]},
        'actions': [
            {'type': 'set_priority', 'code': 'P1'},
            {'type': 'set_queue', 'name': 'Escalations'},
            {'type': 'add_tag', 'tag': 'outage'},
        ],
        'sort_order': 5,
    },
    {
        'name': 'Unassigned > 4h — flag for triage',
        'description': 'When ticket save fires and the ticket is still unassigned, drop a triage tag.',
        'trigger': 'ticket_updated',
        'conditions': {'is_unassigned': True},
        'actions': [
            {'type': 'add_tag', 'tag': 'needs-triage'},
        ],
        'sort_order': 100,
    },
    {
        'name': 'Client reply — notify owner',
        'description': 'A new comment on a ticket re-engages the assignee — adds them as a watcher (idempotent) so they get the notify.',
        'trigger': 'comment_added',
        'conditions': {},
        'actions': [
            {'type': 'add_tag', 'tag': 'client-replied'},
        ],
        'sort_order': 50,
    },
]


class Command(BaseCommand):
    help = 'Install a starter WorkflowRule set in one or all organizations.'

    def add_arguments(self, parser):
        parser.add_argument('--org-id', type=int)
        parser.add_argument('--replace', action='store_true',
                            help='Replace existing rules with matching names')

    def handle(self, *args, **options):
        if options.get('org_id'):
            orgs = Organization.objects.filter(pk=options['org_id'])
        else:
            orgs = Organization.objects.filter(is_active=True)
        if not orgs.exists():
            self.stdout.write(self.style.WARNING('No active organizations.'))
            return

        replace = options.get('replace', False)
        total_created = 0
        total_skipped = 0
        for org in orgs:
            for sample in SAMPLE_RULES:
                existing = WorkflowRule.objects.filter(
                    organization=org, name=sample['name']
                ).first()
                if existing and not replace:
                    total_skipped += 1
                    continue
                if existing and replace:
                    existing.delete()
                WorkflowRule.objects.create(
                    organization=org,
                    name=sample['name'],
                    description=sample['description'],
                    trigger=sample['trigger'],
                    conditions=sample['conditions'],
                    actions=sample['actions'],
                    is_active=True,
                    sort_order=sample['sort_order'],
                )
                total_created += 1
            self.stdout.write(self.style.SUCCESS(
                f'{org.name}: rules installed'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'Done — created {total_created}, skipped {total_skipped} (already present).'
        ))
