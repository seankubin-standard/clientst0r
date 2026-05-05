"""Lenovo Support Warranty adapter — Phase 17 v5 (v3.17.309) stub.

Live lookup_warranty() will POST to /support/v2/warranty with the
serial number. Token auth via the Lenovo SupportNumber API.

API reference: https://supportapi.lenovo.com/v2.5/swagger/index.html
"""
from __future__ import annotations

from typing import Any, Dict

from .base import BaseWarrantyProvider


class LenovoWarrantyProvider(BaseWarrantyProvider):
    provider_type = 'lenovo'
    provider_name = 'Lenovo Support'
    DEFAULT_BASE_URL = 'https://supportapi.lenovo.com'

    def lookup_warranty(self, serial_number: str) -> Dict[str, Any]:
        creds = self.credentials
        if not creds.get('api_key'):
            return {'success': False, 'expires_on': None,
                    'service_level': '',
                    'error': 'Lenovo API key missing'}
        return {
            'success': False,
            'expires_on': None,
            'service_level': '',
            'error': 'Lenovo live lookup not yet implemented in this build',
        }
