"""
Baseline test coverage for the locations/ app.

Tracks physical locations + WAN connections + floor plans for
multi-location clients. Bug = wrong tenant access (shared-location
ACL leak), broken HQ uniqueness (multiple primaries claimed), or
silent address-rendering breakage.

Coverage areas:
  * `Location` model — `is_primary` uniqueness per org (only one HQ
    per organization), `is_shared` enforces `is_primary=False`,
    `__str__` discriminates shared / HQ / regular.
  * `Location.full_address` formatting + `has_coordinates` flag.
  * `Location.can_organization_access` ACL — owner-only by default,
    associated_organizations only for shared.
  * `WAN.is_down`, `bandwidth_display` formatting.
"""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from core.models import Organization
from locations.models import WAN, Location


def _addr_kwargs(**overrides):
    """Common address fields so tests don't repeat them."""
    out = dict(
        street_address='123 Main St',
        city='Austin',
        state='TX',
        postal_code='78701',
        country='United States',
    )
    out.update(overrides)
    return out


class LocationModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name='LocCo', slug='loc-co')

    def test_str_for_owned_location(self):
        loc = Location.objects.create(
            organization=self.org, name='Main', **_addr_kwargs(),
        )
        s = str(loc)
        self.assertIn('Main', s)
        self.assertIn('LocCo', s)

    def test_str_marks_hq_when_primary(self):
        loc = Location.objects.create(
            organization=self.org, name='HQ', is_primary=True, **_addr_kwargs(),
        )
        self.assertIn('(HQ)', str(loc))

    def test_str_marks_shared(self):
        # Shared locations have no `organization` (per the model contract)
        # — leave it null and put the access list on associated_organizations.
        loc = Location.objects.create(
            organization=None, is_shared=True, name='Colo', **_addr_kwargs(),
        )
        loc.associated_organizations.add(self.org)
        self.assertIn('(Shared)', str(loc))

    def test_full_address_includes_required_fields(self):
        loc = Location.objects.create(
            organization=self.org, name='X',
            **_addr_kwargs(street_address_2='Suite 100'),
        )
        addr = loc.full_address
        self.assertIn('123 Main St', addr)
        self.assertIn('Suite 100', addr)
        self.assertIn('Austin', addr)
        self.assertIn('TX', addr)
        self.assertIn('78701', addr)

    def test_full_address_omits_country_when_united_states(self):
        loc = Location.objects.create(
            organization=self.org, name='X', **_addr_kwargs(),
        )
        # United States is the default and shouldn't be appended.
        self.assertNotIn('United States', loc.full_address)

    def test_full_address_includes_country_when_non_us(self):
        loc = Location.objects.create(
            organization=self.org, name='X',
            **_addr_kwargs(country='Canada'),
        )
        self.assertIn('Canada', loc.full_address)

    def test_has_coordinates_true_only_with_lat_and_lng(self):
        loc1 = Location.objects.create(
            organization=self.org, name='no-coords', **_addr_kwargs(),
        )
        loc2 = Location.objects.create(
            organization=self.org, name='with-coords',
            latitude=Decimal('30.2672'), longitude=Decimal('-97.7431'),
            **_addr_kwargs(city='AustinB'),
        )
        self.assertFalse(loc1.has_coordinates)
        self.assertTrue(loc2.has_coordinates)

    def test_setting_is_primary_demotes_other_primaries(self):
        # Only ONE primary location per organization. Saving a new primary
        # must demote the existing one. This is the load-bearing HQ
        # uniqueness invariant.
        first = Location.objects.create(
            organization=self.org, name='Old HQ', is_primary=True, **_addr_kwargs(),
        )
        new = Location.objects.create(
            organization=self.org, name='New HQ', is_primary=True,
            **_addr_kwargs(city='AustinB'),
        )
        first.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertTrue(new.is_primary)

    def test_shared_location_cannot_be_primary(self):
        # Save() forces is_primary=False for shared locations.
        loc = Location.objects.create(
            organization=None, is_shared=True, is_primary=True,
            name='Colo', **_addr_kwargs(),
        )
        self.assertFalse(loc.is_primary)


class LocationAccessControlTests(TestCase):
    """`can_organization_access` is the load-bearing ACL for locations.
    Bug here = wrong tenant gets to see a location."""

    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organization.objects.create(name='ACL-A', slug='acl-a')
        cls.org_b = Organization.objects.create(name='ACL-B', slug='acl-b')

    def test_owner_can_access_owned_location(self):
        loc = Location.objects.create(
            organization=self.org_a, name='A-only', **_addr_kwargs(),
        )
        self.assertTrue(loc.can_organization_access(self.org_a))

    def test_other_org_cannot_access_owned_location(self):
        loc = Location.objects.create(
            organization=self.org_a, name='A-only', **_addr_kwargs(),
        )
        self.assertFalse(loc.can_organization_access(self.org_b))

    def test_associated_org_can_access_shared_location(self):
        shared = Location.objects.create(
            organization=None, is_shared=True, name='Colo', **_addr_kwargs(),
        )
        shared.associated_organizations.add(self.org_a)
        self.assertTrue(shared.can_organization_access(self.org_a))
        self.assertFalse(shared.can_organization_access(self.org_b))

    def test_get_all_organizations_returns_associated_for_shared(self):
        shared = Location.objects.create(
            organization=None, is_shared=True, name='Colo', **_addr_kwargs(),
        )
        shared.associated_organizations.add(self.org_a, self.org_b)
        all_orgs = list(shared.get_all_organizations())
        self.assertIn(self.org_a, all_orgs)
        self.assertIn(self.org_b, all_orgs)

    def test_get_all_organizations_returns_owner_for_non_shared(self):
        loc = Location.objects.create(
            organization=self.org_a, name='A-only', **_addr_kwargs(),
        )
        self.assertEqual(list(loc.get_all_organizations()), [self.org_a])


class WANModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name='WANCo-loc', slug='wan-loc')
        cls.location = Location.objects.create(
            organization=cls.org, name='HQ', **_addr_kwargs(),
        )

    def _wan(self, **overrides):
        defaults = dict(
            organization=self.org, location=self.location,
            name='Primary Fiber', wan_type='fiber',
            isp_name='Acme Net', status='active',
        )
        defaults.update(overrides)
        return WAN.objects.create(**defaults)

    def test_str_includes_location_and_name(self):
        w = self._wan()
        self.assertIn('HQ', str(w))
        self.assertIn('Primary Fiber', str(w))

    def test_is_down_true_when_status_down(self):
        self.assertTrue(self._wan(status='down').is_down)

    def test_is_down_false_when_status_active(self):
        self.assertFalse(self._wan().is_down)

    def test_bandwidth_display_unknown_when_no_speeds(self):
        w = self._wan()
        self.assertEqual(w.bandwidth_display, 'Unknown')

    def test_bandwidth_display_full_when_both_speeds_set(self):
        w = self._wan(bandwidth_download_mbps=1000, bandwidth_upload_mbps=500)
        self.assertIn('1000', w.bandwidth_display)
        self.assertIn('500', w.bandwidth_display)

    def test_bandwidth_display_download_only(self):
        w = self._wan(bandwidth_download_mbps=200)
        self.assertEqual(w.bandwidth_display, '200 Mbps')
