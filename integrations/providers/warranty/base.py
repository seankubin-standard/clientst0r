"""BaseWarrantyProvider — Phase 17 v5 (v3.17.309) interface for vendor
warranty-lookup APIs."""
from __future__ import annotations

import logging
from typing import Any, Dict


logger = logging.getLogger('integrations.warranty')


class WarrantyProviderError(Exception):
    pass


class BaseWarrantyProvider:
    """Subclasses MUST set:
      provider_type
      provider_name
      DEFAULT_BASE_URL

    And SHOULD implement:
      lookup_warranty(serial_number) -> Dict
        Returns {success: bool, expires_on: date|None,
                 service_level: str, error: str|None}
    """
    provider_type = 'base'
    provider_name = 'Base Warranty Provider'
    DEFAULT_BASE_URL = ''

    def __init__(self, connection):
        self.connection = connection
        if not connection.base_url and self.DEFAULT_BASE_URL:
            connection.base_url = self.DEFAULT_BASE_URL

    @property
    def credentials(self) -> Dict[str, Any]:
        return self.connection.get_credentials()

    def test_connection(self) -> bool:
        """Stub: True when an API key / OAuth client is configured."""
        creds = self.credentials
        return bool(creds.get('api_key') or creds.get('client_id'))

    def lookup_warranty(self, serial_number: str) -> Dict[str, Any]:
        raise NotImplementedError(
            f'{self.provider_name} lookup_warranty() not yet wired — '
            f'connect a real account to enable.')
