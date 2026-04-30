"""
Stub for IMAP-based lead capture. Phase 5.3 ships the architecture; the
actual polling logic lands in a follow-up release (Phase 5.4).
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Poll a configured IMAP inbox for inbound lead emails — STUB.'

    def handle(self, *args, **opts):
        self.stdout.write(self.style.WARNING(
            'IMAP lead capture is not yet implemented. Configure SMTP-only '
            'inbound for now via the web form or REST API. See ROADMAP.md '
            'Phase 5.3 follow-up.'
        ))
