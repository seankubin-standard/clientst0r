"""
PSA AI Assist — views (Phase 10a: read-only generate-and-view).

Approve / send / apply flows land in 10b/10c. For 10a we expose:
  * POST /psa/ai/generate-reply/<ticket_number>/
  * GET  /psa/ai/suggestion/<id>/  (detail)
  * POST /psa/ai/suggestion/<id>/reject/  (record rejection + feedback)
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from audit.models import AuditLog
from core.decorators import require_write
from psa.feature_flags import require_psa_enabled
from psa.views import _scoped_ticket_qs

from .models import AISuggestion
from .services.reply_generator import SafetyFailure, generate_reply_for_ticket


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _ai_on(request):
    """Check both the master PSA flag (decorator handles that) AND the AI
    sub-flag. The decorator stack already enforces psa_enabled."""
    from core.models import SystemSetting
    return SystemSetting.get_settings().psa_ai_enabled


def _user_can_view_suggestion(user, suggestion: AISuggestion) -> bool:
    """Tenant-scoped + role-aware visibility."""
    if user.is_superuser or getattr(user, '_is_staff_user_cache', False):
        return True
    profile = getattr(user, 'profile', None)
    if profile is not None and hasattr(profile, 'is_staff_user') and profile.is_staff_user():
        return True
    if not hasattr(user, 'memberships'):
        return False
    return user.memberships.filter(
        organization_id=suggestion.organization_id, is_active=True,
    ).exists()


@login_required
@require_write
@require_psa_enabled
@require_http_methods(['POST'])
def generate_reply(request, ticket_number):
    """Generate a fresh AI reply suggestion for the ticket."""
    if not _ai_on(request):
        raise Http404('AI Assist is not enabled.')

    qs = _scoped_ticket_qs(request)
    ticket = get_object_or_404(qs, ticket_number=ticket_number)

    try:
        suggestion = generate_reply_for_ticket(
            ticket, user=request.user, request_path=request.path,
        )
    except SafetyFailure as exc:
        messages.warning(request, f'AI generation skipped: {exc}')
        return redirect(reverse('psa:ticket_detail', kwargs={'ticket_number': ticket.ticket_number}))

    if suggestion.review_state == 'blocked':
        messages.warning(request, 'AI generated a draft but it was blocked by the safety filter — see the suggestion log for details.')
    elif suggestion.review_state == 'failed':
        messages.error(request, 'AI generation failed (see audit log). Try again in a moment.')
    else:
        messages.success(
            request,
            f'AI reply drafted (confidence {suggestion.confidence:.0%}, risk: {suggestion.risk_level}). Review it before sending.'
        )
    return redirect(reverse('psa:ticket_detail', kwargs={'ticket_number': ticket.ticket_number}))


@login_required
@require_psa_enabled
def suggestion_detail(request, pk):
    """View a single AI suggestion."""
    if not _ai_on(request):
        raise Http404()
    suggestion = get_object_or_404(AISuggestion, pk=pk)
    if not _user_can_view_suggestion(request.user, suggestion):
        raise Http404()
    return JsonResponse({
        'id': suggestion.pk,
        'kind': suggestion.kind,
        'review_state': suggestion.review_state,
        'risk_level': suggestion.risk_level,
        'model_name': suggestion.model_name,
        'confidence': float(suggestion.confidence),
        'suggested_body': suggestion.suggested_body,
        'context_snapshot': suggestion.context_snapshot,
        'created_at': suggestion.created_at.isoformat(),
        'reviewer_note': suggestion.reviewer_note,
    })


@login_required
@require_write
@require_psa_enabled
@require_http_methods(['POST'])
def suggestion_reject(request, pk):
    """Record a rejection + feedback. Phase 10a: rejection is the only
    "act on a suggestion" path; approve+send lands in 10b."""
    if not _ai_on(request):
        raise Http404()
    suggestion = get_object_or_404(AISuggestion, pk=pk)
    if not _user_can_view_suggestion(request.user, suggestion):
        raise Http404()
    if suggestion.review_state not in ('draft', 'pending_review'):
        messages.info(request, 'This suggestion is already in a terminal state.')
        return _back(request, suggestion)

    note = (request.POST.get('reviewer_note') or '').strip()[:2000]
    suggestion.review_state = 'rejected'
    suggestion.reviewer = request.user
    suggestion.reviewed_at = timezone.now()
    suggestion.reviewer_note = note
    suggestion.save(update_fields=[
        'review_state', 'reviewer', 'reviewed_at', 'reviewer_note',
    ])

    AuditLog.log(
        user=request.user, action='update', organization=suggestion.organization,
        object_type='psa_ai.AISuggestion', object_id=suggestion.pk,
        object_repr=f'rejected suggestion {suggestion.pk}',
        description=f'Rejected AI suggestion {suggestion.pk}: {note[:120]}',
        ip_address=_client_ip(request), path=request.path,
        extra_data={'note_length': len(note)},
    )
    messages.success(request, 'Rejected. The feedback is logged for prompt tuning.')
    return _back(request, suggestion)


def _back(request, suggestion: AISuggestion):
    nt = suggestion.native_ticket
    if nt is not None:
        return redirect(reverse('psa:ticket_detail', kwargs={'ticket_number': nt.ticket_number}))
    return redirect('psa:ticket_list')
