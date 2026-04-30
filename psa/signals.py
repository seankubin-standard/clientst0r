"""
PSA signal handlers - fire WorkflowRule engine on ticket / comment events,
plus tech notifications when a ticket gets assigned or scheduled.

Kept minimal: a status change is detected via a pre_save snapshot of the
old status_id, then post_save dispatches the appropriate trigger. Each
handler swallows engine errors so workflow misconfiguration never blocks
ticket save flow.
"""
from __future__ import annotations

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Ticket, TicketComment


logger = logging.getLogger('psa.signals')


# ticket_id -> {status_id, assigned_to_id, resolution_due_at} captured pre_save
_PRIOR_TICKET = {}


@receiver(pre_save, sender=Ticket)
def _capture_prior_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            prev = Ticket.objects.only(
                'status_id', 'assigned_to_id', 'resolution_due_at',
            ).get(pk=instance.pk)
            _PRIOR_TICKET[instance.pk] = {
                'status_id': prev.status_id,
                'assigned_to_id': prev.assigned_to_id,
                'resolution_due_at': prev.resolution_due_at,
            }
        except Ticket.DoesNotExist:
            _PRIOR_TICKET[instance.pk] = {
                'status_id': None,
                'assigned_to_id': None,
                'resolution_due_at': None,
            }
    else:
        _PRIOR_TICKET[instance.pk] = {
            'status_id': None,
            'assigned_to_id': None,
            'resolution_due_at': None,
        }


@receiver(post_save, sender=Ticket)
def _fire_ticket_workflow(sender, instance, created, **kwargs):
    prior = _PRIOR_TICKET.pop(instance.pk, {
        'status_id': None,
        'assigned_to_id': None,
        'resolution_due_at': None,
    })
    try:
        from .workflow_engine import fire
        if created:
            fire('ticket_created', instance)
        else:
            prior_status_id = prior.get('status_id')
            if prior_status_id is not None and prior_status_id != instance.status_id:
                fire('status_changed', instance, prior_status=prior_status_id)
            fire('ticket_updated', instance)
    except Exception:
        logger.exception('PSA ticket workflow signal failed')

    # Tech notifications - never block save flow
    try:
        from .notifications import notify_tech_assigned, notify_tech_scheduled
        by_user = getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None)
        # Assignment changed (including new ticket with an assignee)
        if instance.assigned_to_id and instance.assigned_to_id != prior.get('assigned_to_id'):
            notify_tech_assigned(instance, by_user=by_user)
        # Schedule changed (resolution_due_at set or changed) - only when assigned
        if (
            instance.assigned_to_id
            and instance.resolution_due_at
            and instance.resolution_due_at != prior.get('resolution_due_at')
        ):
            notify_tech_scheduled(
                instance,
                by_user=getattr(instance, 'updated_by', None),
                prior_due_date=prior.get('resolution_due_at'),
            )
    except Exception:
        logger.exception('PSA tech notification signal failed')


@receiver(post_save, sender=TicketComment)
def _fire_comment_workflow(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from .workflow_engine import fire
        fire('comment_added', instance.ticket)
    except Exception:
        logger.exception('PSA comment workflow signal failed')


@receiver(post_save, sender=Ticket)
def _auto_create_change_request(sender, instance, created, **kwargs):
    """When a Ticket of type 'change' is created, auto-spawn a draft
    ChangeRequest. The ticket_type slug 'change' is the link contract."""
    if not created:
        return
    try:
        if instance.ticket_type and instance.ticket_type.slug == 'change':
            from .models import ChangeRequest
            ChangeRequest.objects.get_or_create(
                ticket=instance,
                defaults={'organization': instance.organization},
            )
    except Exception:
        logger.exception('PSA change request auto-create signal failed')
