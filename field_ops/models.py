"""
Phase 8 (Field Ops) — models.

Backend foundation for GPS auto-documentation + timeclock + privacy.

Built across the v3.17.386 → v3.17.395 release train. This module is split
across releases:

- v3.17.386 — TechnicianLocation + ClientSiteGeofence (this file)
- v3.17.387 — TimeclockEntry + MobileDevice
- v3.17.389 — LocationRetentionPolicy
- v3.17.390 — AutoTimePreference
- v3.17.393 — OrganizationFieldOpsSettings (geofence-only mode flag)
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


# -----------------------------------------------------------------------------
# Sub-phase 8.1 — TechnicianLocation
# -----------------------------------------------------------------------------

SOURCE_CHOICES = (
    ('mobile', 'Mobile app'),
    ('web', 'Web browser'),
)


class TechnicianLocation(models.Model):
    """
    Append-only GPS ping from a tech's device. Never updated, only created
    + pruned. Off-shift pings are dropped at the API layer (Phase 8.5) and
    never get a row here.
    """

    tech = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gps_pings',
    )
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.PositiveIntegerField(
        help_text='Reported accuracy radius in meters',
        default=0,
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=12, choices=SOURCE_CHOICES, default='mobile')
    # Pre-computed retention deadline so the prune mgmt cmd is a one-shot
    # WHERE retention_until < today() rather than a per-org join.
    retention_until = models.DateField(db_index=True)

    class Meta:
        verbose_name = 'Technician GPS ping'
        verbose_name_plural = 'Technician GPS pings'
        indexes = [
            models.Index(fields=['tech', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        if not self.retention_until:
            # Default 90 days. The org-level policy (v3.17.389) overrides
            # this when the row is created via the API.
            self.retention_until = (timezone.now().date() + timedelta(days=90))
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.tech_id}@{self.lat},{self.lon} {self.timestamp:%Y-%m-%d %H:%M}'


# -----------------------------------------------------------------------------
# Sub-phase 8.1 — ClientSiteGeofence
# -----------------------------------------------------------------------------

GEOFENCE_KIND_CHOICES = (
    ('radius', 'Radius (lat/lon + meters)'),
    ('polygon', 'Polygon (list of lat/lon vertices)'),
)


class ClientSiteGeofence(models.Model):
    """
    Geofence boundary used to auto-detect "tech is on site" for a client.

    Two modes:
    - radius:  center_lat / center_lon + radius_meters.
    - polygon: polygon_json = [[lat, lon], [lat, lon], ...] (closed ring,
               first vertex repeated implicitly).
    """

    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='geofences',
    )
    # Optional FK to a per-org location (Phase 18 multi-location); soft FK so
    # we don't break installs that don't use multi-location yet.
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geofences',
    )
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=12, choices=GEOFENCE_KIND_CHOICES, default='radius')
    center_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    center_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_meters = models.PositiveIntegerField(default=100)
    polygon_json = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client site geofence'
        verbose_name_plural = 'Client site geofences'
        ordering = ['organization_id', 'name']

    def __str__(self) -> str:
        return f'{self.organization_id}:{self.name}'

    def contains(self, lat: Decimal, lon: Decimal) -> bool:
        """
        Quick membership test. Radius mode uses the equirectangular
        approximation (good enough at MSP scale, ~100m geofences). Polygon
        mode uses ray casting.
        """
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            return False

        if self.kind == 'radius':
            if self.center_lat is None or self.center_lon is None:
                return False
            # Equirectangular: distance ≈ R * sqrt(dlat² + (cos(lat) * dlon)²)
            import math
            R = 6_371_000  # meters
            clat = float(self.center_lat)
            clon = float(self.center_lon)
            dlat = math.radians(lat_f - clat)
            dlon = math.radians(lon_f - clon)
            mlat = math.radians((lat_f + clat) / 2.0)
            x = dlon * math.cos(mlat)
            y = dlat
            distance = R * math.sqrt(x * x + y * y)
            return distance <= float(self.radius_meters)

        if self.kind == 'polygon':
            poly = self.polygon_json or []
            if len(poly) < 3:
                return False
            # Ray casting algorithm.
            inside = False
            n = len(poly)
            j = n - 1
            for i in range(n):
                pi = poly[i]
                pj = poly[j]
                if not (isinstance(pi, (list, tuple)) and len(pi) == 2):
                    continue
                if not (isinstance(pj, (list, tuple)) and len(pj) == 2):
                    continue
                yi, xi = float(pi[0]), float(pi[1])
                yj, xj = float(pj[0]), float(pj[1])
                if ((yi > lat_f) != (yj > lat_f)) and (
                    lon_f < (xj - xi) * (lat_f - yi) / ((yj - yi) or 1e-12) + xi
                ):
                    inside = not inside
                j = i
            return inside

        return False
