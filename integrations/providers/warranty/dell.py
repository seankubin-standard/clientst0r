"""Dell TechDirect Warranty adapter — Phase 17 v5 (v3.17.309) stub.

Live lookup_warranty() will GET /api/asset-entitlements/v1/asset-entitlements
with `servicetags=<serial>` and parse `entitlements` for the latest
endDate.

API reference: https://developer.dell.com/apis/3471/versions/1.0
"""
from __future__ import annotations

from typing import Any, Dict

from .base import BaseWarrantyProvider


class DellWarrantyProvider(BaseWarrantyProvider):
    provider_type = 'dell'
    provider_name = 'Dell TechDirect'
    DEFAULT_BASE_URL = 'https://apigtwb2c.us.dell.com'

    def lookup_warranty(self, serial_number: str) -> Dict[str, Any]:
        creds = self.credentials
        if not (creds.get('client_id') and creds.get('client_secret')):
            return {'success': False, 'expires_on': None,
                    'service_level': '',
                    'error': 'Dell TechDirect OAuth credentials missing'}
        return {
            'success': False,
            'expires_on': None,
            'service_level': '',
            'error': 'Dell live lookup not yet implemented in this build',
        }
