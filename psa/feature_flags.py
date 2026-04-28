"""
Feature-flag helpers for the native PSA module.

PSA is OFF by default at both the system and per-client level. Routes,
background jobs, and navigation must consult these helpers and return
404/PermissionDenied when disabled — never silently expose data.
"""
from functools import wraps

from django.http import Http404
from django.shortcuts import redirect


def is_psa_enabled():
    """True if the PSA feature is globally enabled in SystemSetting."""
    try:
        from core.models import SystemSetting
        settings = SystemSetting.get_settings()
        return bool(getattr(settings, 'psa_enabled', False))
    except Exception:
        # If settings can't be loaded for any reason, fail closed.
        return False


def is_psa_enabled_for_client(organization):
    """
    True if PSA is globally enabled AND specifically enabled for the given
    organization. Default per-org state is disabled.
    """
    if not is_psa_enabled():
        return False
    if organization is None:
        return False
    try:
        from psa.models import ClientPSASettings
        cps = ClientPSASettings.objects.filter(organization=organization).first()
        if cps is None:
            return False
        return bool(cps.enabled)
    except Exception:
        return False


def require_psa_enabled(view_func):
    """
    View decorator: 404 if PSA is globally disabled.
    Use on every PSA route. Pair with @login_required first.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_psa_enabled():
            raise Http404("PSA is not enabled")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_client_psa_enabled(view_func):
    """
    View decorator: 404 if PSA is disabled globally OR for the active
    organization on the request. Use on routes that operate within a
    client/org context.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_psa_enabled():
            raise Http404("PSA is not enabled")
        org = getattr(request, 'current_organization', None)
        if not is_psa_enabled_for_client(org):
            raise Http404("PSA is not enabled for this client")
        return view_func(request, *args, **kwargs)
    return wrapper
