"""
field_ops tests — Phase 8 (GPS auto-time + Timeclock + privacy).
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import Organization

from .models import ClientSiteGeofence, TechnicianLocation


class TechnicianLocationTests(TestCase):
    """v3.17.386 — TechnicianLocation model."""

    def setUp(self):
        self.user = User.objects.create_user(username='tech1', password='x')

    def test_create_location_sets_default_retention(self):
        loc = TechnicianLocation.objects.create(
            tech=self.user,
            lat=Decimal('40.123456'),
            lon=Decimal('-73.987654'),
            accuracy=15,
            source='mobile',
        )
        self.assertIsNotNone(loc.retention_until)
        # Default retention is ~90 days
        delta = (loc.retention_until - timezone.now().date()).days
        self.assertGreaterEqual(delta, 89)
        self.assertLessEqual(delta, 91)

    def test_explicit_retention_preserved(self):
        target = timezone.now().date() + timedelta(days=30)
        loc = TechnicianLocation.objects.create(
            tech=self.user,
            lat=Decimal('40.0'),
            lon=Decimal('-73.0'),
            retention_until=target,
        )
        self.assertEqual(loc.retention_until, target)


class ClientSiteGeofenceTests(TestCase):
    """v3.17.386 — ClientSiteGeofence containment math."""

    def setUp(self):
        self.org = Organization.objects.create(name='Acme Corp')

    def test_radius_geofence_contains_point(self):
        # 100m radius around (40.0, -73.0). Same point -> inside.
        fence = ClientSiteGeofence.objects.create(
            organization=self.org,
            name='Acme HQ',
            kind='radius',
            center_lat=Decimal('40.000000'),
            center_lon=Decimal('-73.000000'),
            radius_meters=100,
        )
        self.assertTrue(fence.contains(Decimal('40.000000'), Decimal('-73.000000')))

    def test_radius_geofence_excludes_distant_point(self):
        fence = ClientSiteGeofence.objects.create(
            organization=self.org,
            name='Acme HQ',
            kind='radius',
            center_lat=Decimal('40.000000'),
            center_lon=Decimal('-73.000000'),
            radius_meters=100,
        )
        # ~100km away — definitely outside
        self.assertFalse(fence.contains(Decimal('41.000000'), Decimal('-74.000000')))

    def test_polygon_geofence_contains_point(self):
        # Square around (40,-73) of width 0.01 deg (~1.1km)
        fence = ClientSiteGeofence.objects.create(
            organization=self.org,
            name='Acme campus',
            kind='polygon',
            polygon_json=[
                [40.005, -73.005],
                [40.005, -72.995],
                [39.995, -72.995],
                [39.995, -73.005],
            ],
        )
        self.assertTrue(fence.contains(Decimal('40.0'), Decimal('-73.0')))
        self.assertFalse(fence.contains(Decimal('41.0'), Decimal('-73.0')))

    def test_admin_str(self):
        fence = ClientSiteGeofence.objects.create(
            organization=self.org,
            name='HQ',
            kind='radius',
            center_lat=Decimal('40.0'),
            center_lon=Decimal('-73.0'),
            radius_meters=100,
        )
        self.assertIn('HQ', str(fence))
