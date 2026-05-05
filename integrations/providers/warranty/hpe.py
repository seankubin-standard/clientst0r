"""HPE iLO Warranty adapter — Phase 17 v5 (v3.17.309) stub.

Live lookup_warranty() will POST to the HPE Support Center warranty API
with the asset's serial number, then parse the response for warranty
end-date and contractType.

API reference: https://developer.hpe.com/platform/warranty/home/
"""
from __future__ import annotations

from typing import Any, Dict

from .base import BaseWarrantyProvider


class HPEWarrantyProvider(BaseWarrantyProvider):
    provider_type = 'hpe'
    provider_name = 'HPE Support Center'
    DEFAULT_BASE_URL = 'https://support.hpe.com'

    def lookup_warranty(self, serial_number: str) -> Dict[str, Any]:
        creds = self.credentials
        if not creds.get('api_key'):
            return {'success': False, 'expires_on': None,
                    'service_level': '',
                    'error': 'HPE API key missing'}
        return {
            'success': False,
            'expires_on': None,
            'service_level': '',
            'error': 'HPE live lookup not yet implemented in this build',
        }
