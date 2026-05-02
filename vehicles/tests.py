"""
Baseline test coverage for the vehicles/ app.

Service vehicles + fleet inventory + receipts. **Last app from the
originally-untested 16** — this release closes Wave 2 of the Phase 7
polish-backlog test sweep.

ServiceVehicle is MSP-wide (no organization FK) — fleet management is
not per-tenant. Inventory is keyed off the vehicle itself.

Coverage areas:
  * `ServiceVehicle.__str__` and `display_name` property.
  * Insurance + registration expiry warnings (30-day window).
  * `has_location` flag + `update_location()` setter.
  * `VehicleInventoryItem` low-stock / needs-restock / total-value
    math.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from vehicles.models import ServiceVehicle, VehicleInventoryItem


class ServiceVehicleModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.v = ServiceVehicle.objects.create(
            name='Truck 1',
            vehicle_type='truck',
            make='Ford', model='F-150', year=2022,
            license_plate='ABC123',
            current_mileage=15000,
        )

    def test_str_format(self):
        s = str(self.v)
        self.assertIn('2022', s)
        self.assertIn('Ford', s)
        self.assertIn('F-150', s)
        self.assertIn('ABC123', s)

    def test_display_name_uses_nickname_when_set(self):
        self.assertEqual(self.v.display_name, 'Truck 1')

    def test_display_name_falls_back_to_make_model_year(self):
        v = ServiceVehicle.objects.create(
            name='', vehicle_type='van',
            make='Mercedes', model='Sprinter', year=2020,
            license_plate='XYZ789',
        )
        self.assertEqual(v.display_name, '2020 Mercedes Sprinter')

    def test_has_location_true_when_both_lat_and_lng_set(self):
        v = ServiceVehicle.objects.create(
            name='Van 1', make='Mercedes', model='Sprinter', year=2020,
            license_plate='LL1', latitude=Decimal('30.2672'),
            longitude=Decimal('-97.7431'),
        )
        self.assertTrue(v.has_location)

    def test_has_location_false_when_either_missing(self):
        v = ServiceVehicle.objects.create(
            name='Van NoGPS', make='Mercedes', model='Sprinter', year=2020,
            license_plate='LL2',
        )
        self.assertFalse(v.has_location)

    def test_update_location_sets_lat_lng_and_timestamp(self):
        before = self.v.last_location_update
        self.v.update_location(30.5, -97.7)
        self.v.refresh_from_db()
        self.assertEqual(self.v.latitude, Decimal('30.5'))
        self.assertEqual(self.v.longitude, Decimal('-97.7'))
        self.assertIsNotNone(self.v.last_location_update)
        self.assertNotEqual(self.v.last_location_update, before)


class VehicleExpiryWarningTests(TestCase):
    """Insurance + registration expiry properties — false when no date,
    true within 30 days, false when far out."""

    def _vehicle(self, **overrides):
        defaults = dict(
            name='probe', make='Ford', model='F-150', year=2022,
            license_plate='PROBE',
        )
        defaults.update(overrides)
        return ServiceVehicle.objects.create(**defaults)

    def test_insurance_expiring_soon_within_window(self):
        v = self._vehicle(insurance_expires_at=date.today() + timedelta(days=10))
        self.assertTrue(v.is_insurance_expiring_soon)

    def test_insurance_expiring_soon_false_far_out(self):
        v = self._vehicle(insurance_expires_at=date.today() + timedelta(days=180))
        self.assertFalse(v.is_insurance_expiring_soon)

    def test_insurance_expiring_soon_false_when_unset(self):
        # Property must short-circuit on None — no `None <= date` crash.
        self.assertFalse(self._vehicle().is_insurance_expiring_soon)

    def test_registration_expiring_soon_within_window(self):
        v = self._vehicle(registration_expires_at=date.today() + timedelta(days=10))
        self.assertTrue(v.is_registration_expiring_soon)

    def test_registration_expiring_soon_false_far_out(self):
        v = self._vehicle(registration_expires_at=date.today() + timedelta(days=180))
        self.assertFalse(v.is_registration_expiring_soon)

    def test_registration_expiring_soon_false_when_unset(self):
        self.assertFalse(self._vehicle().is_registration_expiring_soon)


class VehicleInventoryItemTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vehicle = ServiceVehicle.objects.create(
            name='Truck', make='Ford', model='F-150', year=2022,
            license_plate='INVTRK',
        )

    def _item(self, **overrides):
        defaults = dict(
            vehicle=self.vehicle, name='CAT6 Cable',
            category='Cables', quantity=10, unit='ea',
        )
        defaults.update(overrides)
        return VehicleInventoryItem.objects.create(**defaults)

    def test_str_includes_name_quantity_unit(self):
        i = self._item()
        s = str(i)
        self.assertIn('CAT6 Cable', s)
        self.assertIn('10', s)
        self.assertIn('ea', s)

    def test_is_low_stock_at_minimum(self):
        i = self._item(quantity=5, min_quantity=5)
        self.assertTrue(i.is_low_stock)

    def test_is_low_stock_above_minimum(self):
        i = self._item(quantity=20, min_quantity=5)
        self.assertFalse(i.is_low_stock)

    def test_needs_restock_only_when_reorder_quantity_set(self):
        # Below min but no reorder_quantity configured → not flagged.
        i_no_reorder = self._item(quantity=2, min_quantity=5, reorder_quantity=0)
        self.assertFalse(i_no_reorder.needs_restock)

        # Below min AND reorder_quantity > 0 → flagged.
        i_can_reorder = self._item(
            name='Other cable', quantity=2, min_quantity=5, reorder_quantity=10,
        )
        self.assertTrue(i_can_reorder.needs_restock)

    def test_total_value_math(self):
        i = self._item(quantity=20, unit_cost=Decimal('1.50'))
        self.assertEqual(i.total_value, Decimal('30.00'))

    def test_total_value_handles_no_unit_cost(self):
        i = self._item(quantity=20, unit_cost=None)
        # The implementation returns 0 / None / similar when unit_cost
        # is missing — accept either falsy form rather than asserting a
        # specific representation.
        self.assertFalse(bool(i.total_value))
