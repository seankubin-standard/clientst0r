"""
Mobile API throttles.

`MobileLoginRateThrottle` is the per-IP rate limit for `/api/mobile/v1/auth/login/`.
Reuses the existing `login` scope rate (10/hour) configured in
`config/settings.py::REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`.

`MobileVaultRevealRateThrottle` is the per-user limit for the mobile
`/api/mobile/v1/vault/<id>/reveal/` endpoint. 30/hour, mirroring the
web vault's `@ratelimit(key='user', rate='30/h')` decorator.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class MobileLoginRateThrottle(AnonRateThrottle):
    """Per-IP throttle for mobile login attempts. 10/hour."""
    scope = 'login'


class MobileVaultRevealRateThrottle(UserRateThrottle):
    """Per-authenticated-user throttle on vault password reveals. 30/hour."""
    scope = 'vault_reveal'
