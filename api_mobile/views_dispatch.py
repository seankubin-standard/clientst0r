"""
Mobile API dispatch + scheduling endpoints (v3.17.457).

Surfaces what a tech has on their plate: scheduled tasks they're
assigned to, plus their open tickets. Lets them sign off on assignments
and comment on tasks.
"""
from __future__ import annotations

from django.utils import timezone
from rest_framework import status as drf_status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .scoping import accessible_org_ids


def _serialize_assignment(a) -> dict:
    t = a.task
    return {
        'assignment_id': a.id,
        'task_id': t.id,
        'task_title': t.title,
        'task_description': t.description,
        'task_priority': t.priority,
        'task_status': t.status,
        'task_due_date': t.due_date.isoformat() if t.due_date else None,
        'organization_id': t.organization_id,
        'organization_name': t.organization.name if t.organization_id else None,
        'acknowledged': a.acknowledged,
        'acknowledged_at': a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        'notes': a.notes or '',
        'recurrence': t.recurrence,
    }


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dispatch_board_view(request):
    """
    GET /api/mobile/v1/dispatch/

    Combines scheduled-task assignments + open tickets assigned to the
    caller. Buckets by:
      - overdue:    due_date in the past, not completed
      - today:      due_date inside today's window OR no due_date
      - upcoming:   due_date in the future
      - tickets:    open ticket count + top 5 by -updated_at
    """
    from scheduling.models import TaskAssignment

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    qs = (TaskAssignment.objects
          .filter(user=request.user, task__status__in=['pending', 'in_progress', 'overdue'])
          .select_related('task', 'task__organization'))
    overdue, today, upcoming = [], [], []
    for a in qs:
        d = a.task.due_date
        if d and d < now and a.task.status != 'completed':
            overdue.append(a)
        elif d is None or (today_start <= d < today_end):
            today.append(a)
        else:
            upcoming.append(a)

    # Tickets the user has open work on
    tickets_data = {'open_count': 0, 'recent': []}
    try:
        from psa.models import Ticket
        from .views_tickets import _serialize_ticket
        org_ids = accessible_org_ids(request.user)
        ticket_qs = (Ticket.objects
                     .filter(organization_id__in=org_ids,
                             assigned_to=request.user,
                             status__is_terminal=False)
                     .select_related('status', 'priority'))
        tickets_data['open_count'] = ticket_qs.count()
        tickets_data['recent'] = [
            _serialize_ticket(t) for t in
            ticket_qs.order_by('-updated_at')[:5]
        ]
    except Exception:
        pass

    return Response({
        'overdue':  [_serialize_assignment(a) for a in overdue],
        'today':    [_serialize_assignment(a) for a in today],
        'upcoming': [_serialize_assignment(a) for a in upcoming],
        'tickets':  tickets_data,
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def task_acknowledge_view(request, pk: int):
    """
    POST /api/mobile/v1/dispatch/assignments/<assignment_id>/ack/

    Body: `{notes?}`. Marks this assignment acknowledged. Triggers the
    task's completion check (via `TaskAssignment.sign_off`), which can
    auto-complete the task if `require_all_signoffs` is satisfied.
    """
    from scheduling.models import TaskAssignment

    try:
        a = TaskAssignment.objects.select_related('task').get(
            pk=pk, user=request.user,
        )
    except TaskAssignment.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    notes = (request.data.get('notes') or '').strip()[:2000] if request.data else ''
    a.sign_off(notes=notes)
    a.refresh_from_db()
    return Response(_serialize_assignment(a))


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def task_comment_view(request, pk: int):
    """
    POST /api/mobile/v1/dispatch/tasks/<task_id>/comments/

    Body: `{body}`. Adds a `TaskComment` from the caller.
    """
    from scheduling.models import ScheduledTask, TaskAssignment, TaskComment

    # Caller must have an assignment on this task
    has_assignment = TaskAssignment.objects.filter(
        task_id=pk, user=request.user,
    ).exists()
    if not has_assignment:
        return Response({'detail': 'Not found'}, status=404)

    body = (request.data.get('body') or '').strip() if request.data else ''
    if not body:
        return Response({'detail': 'body is required'}, status=400)

    comment = TaskComment.objects.create(
        task_id=pk, author=request.user, body=body[:5000],
    )
    return Response({
        'id': comment.id,
        'task_id': comment.task_id,
        'author_id': comment.author_id,
        'body': comment.body,
        'created_at': comment.created_at.isoformat() if hasattr(comment, 'created_at') and comment.created_at else None,
    }, status=drf_status.HTTP_201_CREATED)
