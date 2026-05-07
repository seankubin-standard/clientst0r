"""
Mobile API dashboard + organizations endpoints (v3.17.347).
"""
from __future__ import annotations

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .scoping import accessible_org_ids


def _safe_count(model_path, **filters):
    """Count rows defensively — missing app / model returns 0 instead of 500."""
    try:
        from importlib import import_module
        module_name, cls_name = model_path.rsplit('.', 1)
        mod = import_module(module_name)
        Model = getattr(mod, cls_name)
        return Model.objects.filter(**filters).count()
    except Exception:
        return 0


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    """
    GET /api/mobile/v1/dashboard/

    Returns headline counts the mobile dashboard renders. Org-scoped to
    the user's active memberships.
    """
    org_ids = accessible_org_ids(request.user)
    now = timezone.now()
    soon = now + timezone.timedelta(days=30)

    # Tickets
    open_tickets = _safe_count(
        'psa.models.Ticket',
        organization_id__in=org_ids, status__is_terminal=False,
    )
    critical_tickets = _safe_count(
        'psa.models.Ticket',
        organization_id__in=org_ids, status__is_terminal=False,
        priority__code='P1',
    )

    # Expirations (within next 30 days)
    expiring_soon = _safe_count(
        'monitoring.models.Expiration',
        organization_id__in=org_ids, expires_at__lte=soon, expires_at__gte=now,
    )

    # Monitors offline
    offline_monitors = _safe_count(
        'monitoring.models.WebsiteMonitor',
        organization_id__in=org_ids, last_status='down',
    )

    # Recent assets (last 7 days)
    week_ago = now - timezone.timedelta(days=7)
    recent_assets = _safe_count(
        'assets.models.Asset',
        organization_id__in=org_ids, created_at__gte=week_ago,
    )

    # Open security alerts
    security_alerts_open = _safe_count(
        'security_alerts.models.SecurityAlert',
        organization_id__in=org_ids, status='open',
    )

    # Recent activity (audit log entries last 24h)
    day_ago = now - timezone.timedelta(days=1)
    recent_activity = _safe_count(
        'audit.models.AuditLog',
        user=request.user, created_at__gte=day_ago,
    )

    return Response({
        'open_tickets': open_tickets,
        'critical_tickets': critical_tickets,
        'expiring_soon': expiring_soon,
        'offline_monitors': offline_monitors,
        'recent_assets': recent_assets,
        'security_alerts_open': security_alerts_open,
        'recent_activity': recent_activity,
        'organization_count': len(org_ids),
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def organization_list_view(request):
    """
    GET /api/mobile/v1/organizations/?search=&page=

    Paginated list of organizations the user has access to.
    """
    from core.models import Organization

    org_ids = accessible_org_ids(request.user)
    qs = Organization.objects.filter(id__in=org_ids).order_by('name')

    search = (request.query_params.get('search') or '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))

    # Manual pagination — DRF default class would add overhead from a generic view.
    try:
        page = max(int(request.query_params.get('page', 1)), 1)
    except ValueError:
        page = 1
    page_size = 50
    start = (page - 1) * page_size
    total = qs.count()
    rows = qs[start:start + page_size]

    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': [
            {
                'id': o.id,
                'name': o.name,
                'slug': o.slug,
                'organization_type': getattr(o, 'organization_type', '') or '',
            }
            for o in rows
        ],
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def organization_detail_view(request, pk: int):
    """
    GET /api/mobile/v1/organizations/<id>/

    Detail with related counts. Cross-org reads are rejected with 404.
    """
    from core.models import Organization

    org_ids = accessible_org_ids(request.user)
    if pk not in org_ids:
        return Response({'detail': 'Not found'}, status=404)

    try:
        org = Organization.objects.get(pk=pk)
    except Organization.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    asset_count = _safe_count('assets.models.Asset', organization_id=pk)
    ticket_count = _safe_count(
        'psa.models.Ticket', organization_id=pk, status__is_terminal=False,
    )
    contact_count = _safe_count('assets.models.Contact', organization_id=pk)

    return Response({
        'id': org.id,
        'name': org.name,
        'slug': org.slug,
        'organization_type': getattr(org, 'organization_type', '') or '',
        'asset_count': asset_count,
        'open_ticket_count': ticket_count,
        'contact_count': contact_count,
    })
