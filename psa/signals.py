"""
PSA signal handlers — fire WorkflowRule engine on ticket / comment events.

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


_PRIOR_STATUS = {}  # ticket_id → prior status_id during a save


@receiver(pre_save, sender=Ticket)
def _capture_prior_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            prev = Ticket.objects.only('status_id').get(pk=instance.pk)
            _PRIOR_STATUS[instance.pk] = prev.status_id
        except Ticket.DoesNotExist:
            _PRIOR_STATUS[instance.pk] = None
    else:
        _PRIOR_STATUS[instance.pk] = None


@receiver(post_save, sender=Ticket)
def _fire_ticket_workflow(sender, instance, created, **kwargs):
    try:
        from .workflow_engine import fire
        if created:
            fire('ticket_created', instance)
            return
        prior_status_id = _PRIOR_STATUS.pop(instance.pk, None)
        if prior_status_id is not None and prior_status_id != instance.status_id:
            fire('status_changed', instance, prior_status=prior_status_id)
        fire('ticket_updated', instance)
    except Exception:
        logger.exception('PSA ticket workflow signal failed')


@receiver(post_save, sender=TicketComment)
def _fire_comment_workflow(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from .workflow_engine import fire
        fire('comment_added', instance.ticket)
    except Exception:
        logger.exception('PSA comment workflow signal failed')
