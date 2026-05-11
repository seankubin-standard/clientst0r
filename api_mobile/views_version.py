"""
Mobile API version probe (v3.17.472).

Lets the app verify which backend it's hitting, regardless of whether
Apply has run on the server. Anonymous-safe — no auth needed — so the
client can hit it on the login screen too.
"""
from __future__ import annotations

from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def version_view(request):
    """
    GET /api/mobile/v1/version/

    Returns the running server's version + API version. Used by the
    Settings screen to show app-vs-server version side by side so
    you can verify an Apply landed without SSHing in.
    """
    from config.version import VERSION, VERSION_INFO
    return Response({
        'version': VERSION,
        'version_info': VERSION_INFO,
        'api': 'v1',
    })
