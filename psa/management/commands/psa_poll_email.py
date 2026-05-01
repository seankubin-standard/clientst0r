"""
IMAP poller — converts inbound email to PSA tickets.

Designed for cron (every 5 minutes is the default poll_interval). For
each active EmailIngestionConfig:
  1. Connect via IMAP (SSL by default).
  2. Fetch UNREAD messages from the configured folder.
  3. For each message, in order:
       (a) Match In-Reply-To against an existing EmailMessage.message_id
           in the same organization — append the body as a public reply
           comment (Phase 10.1).
       (b) Walk the References chain right-to-left and try the same
           org-scoped Message-ID lookup (Phase 10.1).
       (c) Subject-regex fallback — if `subject_ticket_pattern` matches a
           ticket number we own, append a comment.
       (d) Otherwise create a new Ticket with source='email'.
       Either way, persist an EmailMessage row capturing headers so the
       NEXT inbound reply can thread cleanly.
  4. Mark the message as Seen.

Errors per config are stored on the config row; one bad config doesn't
break the others.
"""
from __future__ import annotations

import email
import imaplib
import logging
import re
from email.header import decode_header
from email.utils import parseaddr, getaddresses

from django.core.management.base import BaseCommand
from django.utils import timezone

from psa.models import (
    EmailIngestionConfig, EmailMessage, Ticket, TicketComment, TicketStatus,
)


logger = logging.getLogger('psa.email_ingest')


def _decode(s) -> str:
    if not s:
        return ''
    if isinstance(s, bytes):
        try:
            return s.decode('utf-8', errors='replace')
        except Exception:
            return str(s)
    return str(s)


def _decode_header(s: str) -> str:
    if not s:
        return ''
    try:
        parts = decode_header(s)
        decoded = []
        for text, charset in parts:
            if isinstance(text, bytes):
                decoded.append(text.decode(charset or 'utf-8', errors='replace'))
            else:
                decoded.append(text)
        return ''.join(decoded)
    except Exception:
        return _decode(s)


def _extract_bodies(msg) -> tuple[str, str]:
    """
    Return (text_body, html_body). Either may be empty. Phase 10.2 will
    swap the crude regex-strip for real HTML sanitization.
    """
    text_body = ''
    html_body = ''
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition') or '')
            if 'attachment' in disp.lower():
                continue
            payload = part.get_payload(decode=True) or b''
            charset = part.get_content_charset() or 'utf-8'
            decoded = payload.decode(charset, errors='replace')
            if ctype == 'text/plain' and not text_body:
                text_body = decoded
            elif ctype == 'text/html' and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True) or b''
        charset = msg.get_content_charset() or 'utf-8'
        decoded = payload.decode(charset, errors='replace')
        if (msg.get_content_type() or '').lower() == 'text/html':
            html_body = decoded
        else:
            text_body = decoded

    if not text_body and html_body:
        text_body = re.sub(r'<[^>]+>', '', html_body)  # Phase 10.2 → bleach
    return text_body, html_body


def _extract_text_body(msg) -> str:
    """Compatibility shim — preserves the v3.17.166 callable signature."""
    text, _ = _extract_bodies(msg)
    return text


def _thread_target(msg, organization) -> Ticket | None:
    """
    Header-based threading. Returns the matching Ticket or None.

    Order: In-Reply-To first, then walk References right-to-left.
    Cross-org isolation is enforced by the organization filter on the
    EmailMessage lookup — org A's Message-ID never resolves a ticket in
    org B, even on collision.
    """
    in_reply_to = (msg.get('In-Reply-To') or '').strip()
    if in_reply_to:
        match = (EmailMessage.objects
                 .filter(organization=organization, message_id=in_reply_to)
                 .select_related('ticket')
                 .first())
        if match:
            return match.ticket

    references = msg.get('References') or ''
    for ref_id in reversed(EmailMessage.parse_references(references)):
        match = (EmailMessage.objects
                 .filter(organization=organization, message_id=ref_id)
                 .select_related('ticket')
                 .first())
        if match:
            return match.ticket
    return None


class Command(BaseCommand):
    help = 'Poll IMAP mailboxes for active EmailIngestionConfig rows and create tickets.'

    def add_arguments(self, parser):
        parser.add_argument('--config-id', type=int)

    def handle(self, *args, **options):
        qs = EmailIngestionConfig.objects.filter(is_active=True)
        if options.get('config_id'):
            qs = qs.filter(pk=options['config_id'])

        if not qs.exists():
            self.stdout.write(self.style.WARNING('No active email-ingestion configs.'))
            return

        new_status = TicketStatus.objects.filter(slug='new').first()
        if new_status is None:
            self.stdout.write(self.style.ERROR('Run psa_seed_defaults first — no "new" TicketStatus.'))
            return

        for config in qs.select_related('default_queue', 'default_priority',
                                        'default_type', 'organization'):
            try:
                created, replied = self._poll_one(config, new_status)
            except Exception as exc:
                config.last_poll_status = 'error'
                config.last_error = str(exc)[:1000]
                config.last_poll_at = timezone.now()
                config.save(update_fields=['last_poll_status', 'last_error', 'last_poll_at'])
                self.stdout.write(self.style.ERROR(f'{config.name}: {exc}'))
                logger.exception('email poll failed for config %s', config.pk)
                continue

            config.last_poll_status = 'ok'
            config.last_error = ''
            config.last_poll_at = timezone.now()
            config.save(update_fields=['last_poll_status', 'last_error', 'last_poll_at'])
            self.stdout.write(self.style.SUCCESS(
                f'{config.name}: created {created} new + {replied} reply comment(s)'
            ))

    def _poll_one(self, config, new_status):
        password = config.get_password()
        if not password:
            raise RuntimeError('No password configured')

        if config.use_ssl:
            mail = imaplib.IMAP4_SSL(config.imap_host, config.imap_port)
        else:
            mail = imaplib.IMAP4(config.imap_host, config.imap_port)
        mail.login(config.username, password)
        try:
            mail.select(config.folder)
            typ, data = mail.search(None, 'UNSEEN')
            if typ != 'OK':
                return 0, 0
            ids = (data[0] or b'').split()

            ticket_pattern = re.compile(config.subject_ticket_pattern)
            created_count = 0
            replied_count = 0

            for msg_id in ids:
                typ, msg_data = mail.fetch(msg_id, '(RFC822)')
                if typ != 'OK' or not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                subject = _decode_header(msg.get('Subject', '')).strip()[:300]
                from_name, from_email = parseaddr(_decode_header(msg.get('From', '')))
                text_body, html_body = _extract_bodies(msg)
                body = text_body.strip()[:50000]

                message_id_hdr = (msg.get('Message-ID') or '').strip()[:998]
                in_reply_to_hdr = (msg.get('In-Reply-To') or '').strip()[:998]
                references_hdr = msg.get('References') or ''

                # Threading order:
                # 1. In-Reply-To / References against existing EmailMessage rows
                # 2. Subject-regex fallback (legacy tickets without captured headers)
                # 3. New ticket
                target = _thread_target(msg, config.organization)
                if target is None:
                    m = ticket_pattern.search(subject)
                    if m:
                        target = Ticket.objects.filter(
                            ticket_number=m.group(0),
                            organization=config.organization,
                        ).first()

                if target is not None:
                    TicketComment.objects.create(
                        ticket=target,
                        body=body or '(empty email body)',
                        is_internal=False,
                        is_system=False,
                        author_name=from_name or from_email or 'email',
                        author_email=from_email or '',
                        source='email',
                    )
                    replied_count += 1
                else:
                    target = Ticket.objects.create(
                        organization=config.organization,
                        subject=subject or '(no subject)',
                        description=body,
                        queue=config.default_queue,
                        priority=config.default_priority,
                        ticket_type=config.default_type,
                        status=new_status,
                        source='email',
                        visibility='client',
                        client_can_view=True,
                        requester_name=from_name[:200] if from_name else '',
                        requester_email=from_email[:254] if from_email else '',
                    )
                    created_count += 1

                # Persist the inbound EmailMessage so the NEXT reply threads
                # cleanly. Skip silently when Message-ID is missing or already
                # seen — we don't want a single buggy mail client to crash
                # the poll loop.
                if message_id_hdr:
                    to_addrs = [addr for _, addr in
                                getaddresses([_decode_header(msg.get('To', '')),
                                              _decode_header(msg.get('Cc', ''))])
                                if addr]
                    EmailMessage.objects.get_or_create(
                        organization=config.organization,
                        message_id=message_id_hdr,
                        defaults={
                            'ticket': target,
                            'ingestion_config': config,
                            'direction': 'in',
                            'in_reply_to': in_reply_to_hdr,
                            'references': references_hdr[:8000],
                            'from_email': (from_email or '')[:320],
                            'to_emails': to_addrs[:50],
                            'subject': subject[:998],
                            'headers_raw': '\n'.join(f'{k}: {v}' for k, v in msg.items())[:16000],
                            'body_text': text_body[:50000],
                            'body_html': html_body[:200000],
                        },
                    )
                    if target.last_inbound_message_id != message_id_hdr:
                        target.last_inbound_message_id = message_id_hdr
                        target.save(update_fields=['last_inbound_message_id'])

                mail.store(msg_id, '+FLAGS', '\\Seen')

            return created_count, replied_count
        finally:
            try:
                mail.logout()
            except Exception:
                pass
