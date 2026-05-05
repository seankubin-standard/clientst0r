"""
Phase 17 v5 (v3.17.309) — vendor warranty lookup adapters.

Dell + HPE + Lenovo stubs ship today. Live API calls land when an
MSP wires up real credentials.
"""
from .base import BaseWarrantyProvider, WarrantyProviderError
from .dell import DellWarrantyProvider
from .hpe import HPEWarrantyProvider
from .lenovo import LenovoWarrantyProvider


PROVIDER_REGISTRY = {
    'dell': DellWarrantyProvider,
    'hpe': HPEWarrantyProvider,
    'lenovo': LenovoWarrantyProvider,
}


def get_warranty_provider(connection):
    cls = PROVIDER_REGISTRY.get(connection.provider_type)
    if cls is None:
        return None
    return cls(connection)
