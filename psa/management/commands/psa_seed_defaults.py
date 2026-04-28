"""
Seed default PSA reference data: queues, statuses, priorities, ticket types,
plus service-catalog items.

Idempotent — safe to run repeatedly. Uses get_or_create so existing
operator-customised rows are preserved.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from psa.models import (
    Queue, ServiceCatalogItem, TicketPriority, TicketStatus, TicketType,
)


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

# (name, description, default_subject, default_body, type_name, queue_name, priority_code, icon)
CATALOG = [
    ('New User', 'Create accounts and access for a new employee.',
     'New user setup — {{name}}', 'Please create accounts for the new user.\n\nFull name:\nEmail:\nManager:\nStart date:\nGroups / licenses:\nEquipment needed:',
     'Onboarding', 'Helpdesk', 'P3', 'fas fa-user-plus'),
    ('Terminate User', 'Disable / off-board a leaving employee.',
     'User termination — {{name}}', 'Please disable accounts and reclaim equipment.\n\nFull name:\nLast day:\nReason:\nForward email to:\nReassign data to:',
     'Offboarding', 'Helpdesk', 'P2', 'fas fa-user-slash'),
    ('Password Reset', 'Reset an existing user account password.',
     'Password reset', 'Account requiring reset:\nUser identity verified by:',
     'Service Request', 'Helpdesk', 'P3', 'fas fa-key'),
    ('MFA Reset', 'Re-enroll multi-factor authentication for a user.',
     'MFA reset', 'User:\nIdentity verification method:',
     'Service Request', 'Helpdesk', 'P3', 'fas fa-mobile-alt'),
    ('Software Install', 'Install or update software on a workstation/server.',
     'Software install', 'User / asset:\nSoftware + version:\nLicense source:',
     'Change Request', 'Helpdesk', 'P3', 'fas fa-download'),
    ('New Computer', 'Provision and ship a new workstation.',
     'New computer for {{user}}', 'User:\nRole / requirements:\nDelivery address:\nApps to pre-install:',
     'Procurement', 'Procurement', 'P3', 'fas fa-laptop'),
    ('Printer Issue', 'Diagnose and resolve printer / MFP problem.',
     'Printer issue', 'Printer model + location:\nError message:\nWhen did it start:',
     'Incident', 'Helpdesk', 'P3', 'fas fa-print'),
    ('VPN Access', 'Grant or troubleshoot VPN.',
     'VPN access', 'User:\nDevice:\nIssue / request:',
     'Access Request', 'Helpdesk', 'P3', 'fas fa-shield-alt'),
    ('Firewall Change', 'Change a firewall rule.',
     'Firewall change request', 'Source:\nDestination:\nPort / protocol:\nDirection:\nReason:\nApproved by:',
     'Change Request', 'Security', 'P2', 'fas fa-fire'),
    ('DNS Change', 'Add / edit / remove a DNS record.',
     'DNS change request', 'Domain:\nRecord type / name / value:\nTTL:\nReason:',
     'Change Request', 'Helpdesk', 'P3', 'fas fa-globe'),
    ('Shared Mailbox', 'Create or modify a shared mailbox.',
     'Shared mailbox request', 'Mailbox name + alias:\nMembers:\nDelegates:\nRetention:',
     'Service Request', 'Helpdesk', 'P3', 'fas fa-envelope'),
    ('Backup Restore', 'Restore data from backup.',
     'Backup restore request', 'What to restore:\nFrom when:\nDestination:\nUser requesting:',
     'Service Request', 'Helpdesk', 'P2', 'fas fa-database'),
    ('SSL Renewal', 'Renew an SSL/TLS certificate.',
     'SSL renewal', 'Hostname / cert subject:\nExpiry:\nProvider:',
     'Change Request', 'Helpdesk', 'P3', 'fas fa-lock'),
    ('Vendor Access', 'Grant short-term access to a third-party vendor.',
     'Vendor access', 'Vendor:\nAccess level:\nDuration:\nReason:\nApproved by:',
     'Access Request', 'Security', 'P2', 'fas fa-handshake'),
    ('Security Incident', 'Suspected breach / phishing / malware.',
     'Security incident', 'What was observed:\nAffected user / asset:\nWhen:\nActions taken so far:',
     'Security Event', 'Security', 'P1', 'fas fa-bug'),
    ('Schedule Onsite Visit', 'Dispatch a technician to a client site.',
     'Onsite visit request', 'Site address:\nDate / time:\nTech needed:\nWork to perform:',
     'Calendar Dispatch', 'Helpdesk', 'P3', 'fas fa-truck'),
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

        # Service catalog
        for i, (name, desc, subj, body, type_name, queue_name, prio_code, icon) in enumerate(CATALOG):
            _, created = ServiceCatalogItem.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slugify(name),
                    'description': desc,
                    'default_subject': subj,
                    'default_body': body,
                    'default_type': TicketType.objects.filter(name=type_name).first(),
                    'default_queue': Queue.objects.filter(name=queue_name).first(),
                    'default_priority': TicketPriority.objects.filter(code=prio_code).first(),
                    'icon': icon,
                    'sort_order': i,
                    'is_active': True,
                },
            )
            created_total += 1 if created else 0
            existing_total += 0 if created else 1

        self.stdout.write(self.style.SUCCESS(
            f'PSA seed complete — {created_total} created, {existing_total} already existed.'
        ))
