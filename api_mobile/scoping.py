"""
Shared helpers for org-scoped queries on the mobile API.

`accessible_org_ids(user)` returns the set of organization IDs the user
has an active Membership for. All list endpoints filter by this set so
a user from Org A cannot list / read rows from Org B even by guessing
the primary key.
"""
from __future__ import annotations

from django.contrib.auth.models import User


def accessible_org_ids(user: User):
    """Return the queryset of org IDs the user has active memberships in."""
    if not user or not user.is_authenticated:
        return []
    try:
        return list(
            user.memberships.filter(is_active=True).values_list('organization_id', flat=True)
        )
    except Exception:
        return []


def in_user_orgs(user: User, qs, field='organization_id'):
    """Filter `qs` to rows whose `field` is in the user's accessible orgs."""
    return qs.filter(**{f'{field}__in': accessible_org_ids(user)})
