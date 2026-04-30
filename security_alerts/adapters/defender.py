"""
Microsoft Defender for Endpoint — REFERENCE adapter.

This is a stub showing where vendor-specific code plugs in. The actual
Microsoft Graph API call is intentionally not implemented; the framework
runs cleanly with an empty alert list and operators can flesh out the
wiring per their tenant.
"""
from integrations.sdk.registry import register
from .base import SecurityProvider


@register
class DefenderForEndpoint(SecurityProvider):
    slug = 'security_defender'
    label = 'Microsoft Defender for Endpoint'
    category = 'security_edr'
    icon = 'fa-shield-virus'

    def test_connection(self, connection):
        # TODO: actual Microsoft Graph token + GET /alerts
        if not connection.base_url:
            return {'ok': False, 'message': 'Missing base_url'}
        return {'ok': True, 'message': 'Stub adapter — connection metadata present'}

    def poll_alerts(self, connection, since=None):
        # TODO: implement Graph API call to /security/alerts_v2 with
        # filter on lastUpdateDateTime > since. Return normalized dicts.
        # For now: return empty list so the framework runs cleanly.
        return []
