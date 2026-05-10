"""
Mobile API assets endpoints (v3.17.348; create endpoint added v3.17.454).
"""
from __future__ import annotations

from django.db.models import Q
from rest_framework import status as drf_status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .scoping import accessible_org_ids


# Whitelist of fields the mobile create endpoint accepts. Anything not
# listed is silently dropped — keeps mobile from setting administrative
# fields like `organization_id` mismatching, audit-only metadata, etc.
_CREATABLE_FIELDS = (
    'name', 'asset_type', 'asset_tag', 'serial_number',
    'hostname', 'ip_address', 'mac_address',
    'os_name', 'os_version', 'manufacturer', 'model',
    'notes',
)


def _serialize_asset(asset, *, detail=False):
    out = {
        'id': asset.id,
        'name': asset.name,
        'asset_type': asset.asset_type,
        'asset_tag': asset.asset_tag,
        'serial_number': asset.serial_number,
        'hostname': asset.hostname,
        'ip_address': asset.ip_address,
        'organization_id': asset.organization_id,
    }
    if detail:
        out.update({
            'mac_address': asset.mac_address,
            'os_name': asset.os_name,
            'os_version': asset.os_version,
            'manufacturer': asset.manufacturer,
            'model': asset.model,
            'warranty_status': getattr(asset, 'warranty_status', '') or '',
            'created_at': asset.created_at.isoformat() if asset.created_at else None,
        })
    return out


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def asset_list_view(request):
    """
    GET  /api/mobile/v1/assets/?search=&organization_id=&type=&status=&page=
    POST /api/mobile/v1/assets/   — create a new asset (v3.17.454)

    Paginated list scoped to the user's accessible organizations. POST
    body: `{organization_id, name, asset_type?, hostname?, ip_address?,
            mac_address?, serial_number?, asset_tag?, os_name?, model?,
            manufacturer?, notes?}`. `organization_id` must be one of the
    user's accessible orgs (403 otherwise); `name` required.
    """
    from assets.models import Asset

    if request.method == 'POST':
        return _create_asset(request)

    org_ids = accessible_org_ids(request.user)
    qs = Asset.objects.filter(organization_id__in=org_ids)

    search = (request.query_params.get('search') or '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(hostname__icontains=search)
            | Q(ip_address__icontains=search)
            | Q(serial_number__icontains=search)
            | Q(asset_tag__icontains=search)
        )

    organization_id = request.query_params.get('organization_id')
    if organization_id:
        try:
            org_id = int(organization_id)
            if org_id in org_ids:
                qs = qs.filter(organization_id=org_id)
            else:
                qs = qs.none()  # asking for an org we don't have access to
        except ValueError:
            pass

    asset_type = request.query_params.get('type')
    if asset_type:
        qs = qs.filter(asset_type=asset_type)

    qs = qs.order_by('name')

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
        'results': [_serialize_asset(a) for a in rows],
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def asset_detail_view(request, pk: int):
    """
    GET /api/mobile/v1/assets/<id>/

    Cross-org reads return 404.
    """
    from assets.models import Asset

    org_ids = accessible_org_ids(request.user)
    try:
        asset = Asset.objects.get(pk=pk, organization_id__in=org_ids)
    except Asset.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    return Response(_serialize_asset(asset, detail=True))


def _create_asset(request):
    """v3.17.454: backing for `POST /assets/`. Helper kept private to
    this module so the public surface stays a single `asset_list_view`."""
    from assets.models import Asset

    org_ids = list(accessible_org_ids(request.user))
    data = request.data or {}

    # organization_id required + must be accessible
    org_id_raw = data.get('organization_id')
    try:
        org_id = int(org_id_raw) if org_id_raw is not None else None
    except (TypeError, ValueError):
        return Response({'detail': 'invalid organization_id'},
                        status=drf_status.HTTP_400_BAD_REQUEST)
    if org_id is None:
        return Response({'detail': 'organization_id is required'},
                        status=drf_status.HTTP_400_BAD_REQUEST)
    if org_id not in org_ids:
        return Response({'detail': 'organization not accessible'},
                        status=drf_status.HTTP_403_FORBIDDEN)

    # name required
    name = (data.get('name') or '').strip()
    if not name:
        return Response({'detail': 'name is required'},
                        status=drf_status.HTTP_400_BAD_REQUEST)

    # Build kwargs from the whitelist; coerce empty strings to ''
    fields = {'organization_id': org_id, 'name': name}
    for key in _CREATABLE_FIELDS:
        if key == 'name':
            continue
        if key in data and data[key] is not None:
            fields[key] = data[key]

    # ip_address: model field is GenericIPAddressField with null=True; '' is invalid
    if fields.get('ip_address') == '':
        fields.pop('ip_address')

    try:
        asset = Asset.objects.create(**fields)
    except Exception as exc:
        return Response(
            {'detail': f'Could not create asset: {exc}'},
            status=drf_status.HTTP_400_BAD_REQUEST,
        )

    return Response(_serialize_asset(asset, detail=True),
                    status=drf_status.HTTP_201_CREATED)
