"""
SLA computation helpers.

Phase 2c keeps it pragmatic: due-dates are computed from the priority's
`response_target_minutes` / `resolution_target_minutes`, anchored at
`Ticket.created_at`. Business hours and holidays land in a later phase
(needs a calendar source we don't yet have).

Pause logic: if the current ticket status has `pauses_sla=True`
(Waiting on Client / Vendor), the SLA is considered paused — we
extend the due-date by the pause duration on resume. For Phase 2c we
keep it simple: a paused status just suppresses the breach badge in
the UI; full pause-and-resume accounting comes with the workflow
engine.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone


def compute_due_dates(ticket):
    """Return (first_response_due_at, resolution_due_at) — both UTC dt
    or None if priority has no targets."""
    if ticket.priority_id is None:
        return None, None
    base = ticket.created_at or timezone.now()
    rt = int(getattr(ticket.priority, 'response_target_minutes', 0) or 0)
    res = int(getattr(ticket.priority, 'resolution_target_minutes', 0) or 0)
    return (
        base + timedelta(minutes=rt) if rt else None,
        base + timedelta(minutes=res) if res else None,
    )


def apply_due_dates(ticket, *, save=True):
    """Set the due-date columns from the priority. Used on create + when
    priority changes."""
    fr, res = compute_due_dates(ticket)
    ticket.first_response_due_at = fr
    ticket.resolution_due_at = res
    if save:
        ticket.save(update_fields=['first_response_due_at', 'resolution_due_at', 'updated_at'])


def is_paused(ticket):
    return bool(ticket.status_id and ticket.status.pauses_sla)


def is_resolved(ticket):
    return bool(ticket.resolved_at) or (ticket.status_id and ticket.status.is_terminal)


def response_breached(ticket, *, now=None):
    """True if the response SLA is breached AND we haven't yet responded."""
    if not ticket.first_response_due_at:
        return False
    if ticket.first_response_at is not None:
        # Already responded — was it on time?
        return ticket.first_response_at > ticket.first_response_due_at
    if is_paused(ticket):
        return False
    return (now or timezone.now()) > ticket.first_response_due_at


def resolution_breached(ticket, *, now=None):
    if not ticket.resolution_due_at:
        return False
    if ticket.resolved_at is not None:
        return ticket.resolved_at > ticket.resolution_due_at
    if is_paused(ticket) or is_resolved(ticket):
        # Paused means clock isn't running; resolved means done.
        return False
    return (now or timezone.now()) > ticket.resolution_due_at


def status_chip(ticket, *, now=None):
    """
    Return a dict for the UI: {kind, label, due_at, minutes_remaining}.
    `kind` ∈ {'breached', 'warning', 'on_track', 'paused', 'resolved', 'no_sla'}.
    Warning threshold = 25% of the resolution window remaining.
    """
    now = now or timezone.now()
    if is_resolved(ticket):
        return {'kind': 'resolved', 'label': 'Resolved'}
    if is_paused(ticket):
        return {'kind': 'paused', 'label': f'Paused ({ticket.status.name})'}
    if not ticket.resolution_due_at:
        return {'kind': 'no_sla', 'label': 'No SLA'}

    if response_breached(ticket, now=now) or resolution_breached(ticket, now=now):
        which = 'response' if response_breached(ticket, now=now) and not ticket.first_response_at else 'resolution'
        return {'kind': 'breached', 'label': f'SLA breached ({which})',
                'due_at': ticket.resolution_due_at}

    # Warning: < 25% of resolution window remaining
    if ticket.resolution_due_at and ticket.created_at:
        total = (ticket.resolution_due_at - ticket.created_at).total_seconds()
        remaining = (ticket.resolution_due_at - now).total_seconds()
        if total > 0 and remaining / total < 0.25:
            mins_left = int(max(0, remaining // 60))
            return {'kind': 'warning', 'label': f'SLA warning — {mins_left} min left',
                    'due_at': ticket.resolution_due_at,
                    'minutes_remaining': mins_left}

    remaining = (ticket.resolution_due_at - now).total_seconds()
    mins_left = int(max(0, remaining // 60))
    return {'kind': 'on_track', 'label': f'On track — {mins_left} min',
            'due_at': ticket.resolution_due_at, 'minutes_remaining': mins_left}


# -- Hygiene flags ----------------------------------------------------------

def hygiene_flags(ticket):
    """Return a list of {key, message} dicts describing hygiene issues
    on this ticket. Used to surface "things to fix before close" hints."""
    flags = []
    if not ticket.assigned_to_id:
        flags.append({'key': 'unassigned', 'message': 'No assignee'})
    if ticket.related_asset_id is None and ticket.organization.assets.exists() if hasattr(ticket.organization, 'assets') else False:
        flags.append({'key': 'no_asset', 'message': 'No asset linked (this client has assets)'})
    if not ticket.time_entries.exists():
        flags.append({'key': 'no_time', 'message': 'No time logged'})
    if ticket.first_response_due_at and not ticket.first_response_at and not is_paused(ticket):
        flags.append({'key': 'no_first_response', 'message': 'No first response yet'})
    return flags


# ---------------------------------------------------------------------------
# Recurring-issue detection (Phase 2c)
# ---------------------------------------------------------------------------

def find_similar_tickets(ticket, *, window_days=90, limit=5):
    """
    Cheap similarity match: same client + same asset (if set) + token
    overlap on subject. Returns list of (ticket, score) tuples sorted by
    score desc. Does not pull pgvector or external services — Phase 4
    can swap in something fancier.
    """
    from datetime import timedelta
    from django.db.models import Q
    from django.utils import timezone as _tz
    from psa.models import Ticket

    cutoff = _tz.now() - timedelta(days=window_days)
    qs = Ticket.objects.filter(
        organization=ticket.organization,
        created_at__gte=cutoff,
    ).exclude(pk=ticket.pk).order_by('-created_at')

    if ticket.related_asset_id:
        # Same-asset hits are strong signals — check those first.
        same_asset = list(qs.filter(related_asset_id=ticket.related_asset_id)[:limit])
    else:
        same_asset = []

    # Token overlap on subject — keep tokens >= 4 chars to drop noise words
    subject_tokens = {t.lower() for t in (ticket.subject or '').split() if len(t) >= 4}
    candidates = list(qs.exclude(pk__in=[t.pk for t in same_asset])[:200])

    scored = []
    for cand in candidates:
        cand_tokens = {t.lower() for t in (cand.subject or '').split() if len(t) >= 4}
        if not cand_tokens or not subject_tokens:
            continue
        overlap = len(subject_tokens & cand_tokens)
        if overlap == 0:
            continue
        # Jaccard-ish score
        score = overlap / float(len(subject_tokens | cand_tokens))
        if score >= 0.3:
            scored.append((cand, round(score, 2)))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    out = [(t, 1.0) for t in same_asset] + scored
    return out[:limit]
