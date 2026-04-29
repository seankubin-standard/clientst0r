"""Template helpers for the docs / KB UI."""
from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    """Dict lookup by key — returns [] for missing or non-dict.

    Used by the recursive KB category tree partial to safely descend
    into ``cats_by_parent[node.id]`` without raising on leaves.
    """
    if isinstance(d, dict):
        return d.get(key, [])
    return []
