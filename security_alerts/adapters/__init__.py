"""
Vendor adapters package — Phase 9 security alert ingestion.

Each adapter module registers a `SecurityProvider` subclass with the
shared Integration SDK registry (`integrations.sdk.registry`). Importing
this package side-effects the full registration so the polling cron and
webhook receiver can resolve adapters by slug.
"""
from .base import SecurityProvider, _maybe_auto_ticket  # noqa: F401

# Reference adapters — import to trigger @register decorator side-effects.
from . import defender  # noqa: F401
