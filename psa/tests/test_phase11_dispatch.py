"""
Phase 11 — Advanced Dispatch & Technician Scheduling tests.

11.1 — Dispatch prioritization (priority + SLA proximity sort) + SLA-burn
panel (open tickets due within 4 hours surface above the grid).

Subsequent sub-phases (PTO conflict awareness, calendar conflict
detection, recurring onsite, geo-aware routing, etc.) will append to
this module.
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.models import Membership, Role
from core.models import Organization, SystemSetting
from psa.models import (
    ClientPSASettings,
    Queue,
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketType,
)
from psa.tests._base import (
    TEST_MIDDLEWARE,
    _setup_seed,
    _enable_psa_global,
    _enable_psa_for,
)


def _make_ticket(*, org, priority, status, queue, ttype,
                  subject='t', resolution_due_at=None, first_response_due_at=None,
                  assigned_to=None):
    return Ticket.objects.create(
        organization=org, subject=subject,
        queue=queue, priority=priority, ticket_type=ttype, status=status,
        resolution_due_at=resolution_due_at,
        first_response_due_at=first_response_due_at,
        assigned_to=assigned_to,
    )


class DispatchPriorityKeyTests(TestCase):
    """The pure-function sort key — no view rendering, just the ordering
    contract."""

    @classmethod
    def setUpTestData(cls):
        _setup_seed()
        cls.org = Organization.objects.create(name='Sort', slug='sort')
        cls.queue = Queue.objects.first()
        cls.status = TicketStatus.objects.filter(slug='new').first()
        cls.ttype = TicketType.objects.first()
        # Two priorities at known sort-orders. Seed defaults already include P1-P5.
        cls.p_high = TicketPriority.objects.order_by('sort_order').first()
        cls.p_low = TicketPriority.objects.order_by('-sort_order').first()
        cls.now = timezone.now()

    def test_higher_priority_sorts_before_lower(self):
        from psa.views import _dispatch_priority_key
        t_high = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
            resolution_due_at=self.now + timedelta(days=1),
        )
        t_low = _make_ticket(
            org=self.org, priority=self.p_low, status=self.status,
            queue=self.queue, ttype=self.ttype,
            resolution_due_at=self.now + timedelta(hours=1),
        )
        # `t_low` is due sooner but has lower priority — `t_high` still wins.
        ordered = sorted([t_low, t_high], key=_dispatch_priority_key)
        self.assertEqual(ordered[0], t_high)

    def test_within_priority_sooner_due_sorts_first(self):
        from psa.views import _dispatch_priority_key
        t_far = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
            resolution_due_at=self.now + timedelta(days=3),
        )
        t_near = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
            resolution_due_at=self.now + timedelta(hours=2),
        )
        ordered = sorted([t_far, t_near], key=_dispatch_priority_key)
        self.assertEqual(ordered[0], t_near)

    def test_no_due_date_sorts_last_within_priority(self):
        from psa.views import _dispatch_priority_key
        t_due = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
            resolution_due_at=self.now + timedelta(days=1),
        )
        t_no_due = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
        )
        ordered = sorted([t_no_due, t_due], key=_dispatch_priority_key)
        self.assertEqual(ordered[0], t_due)
        self.assertEqual(ordered[1], t_no_due)

    def test_first_response_due_used_when_no_resolution_due(self):
        from psa.views import _dispatch_priority_key
        t_resolution = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
            resolution_due_at=self.now + timedelta(hours=10),
        )
        t_response = _make_ticket(
            org=self.org, priority=self.p_high, status=self.status,
            queue=self.queue, ttype=self.ttype,
            first_response_due_at=self.now + timedelta(hours=2),
        )
        ordered = sorted([t_resolution, t_response], key=_dispatch_priority_key)
        self.assertEqual(ordered[0], t_response)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class DispatchSlaBurnPanelTests(TestCase):
    """Open tickets whose due time is within the next 4 hours surface in
    the SLA-burn panel above the grid. Already-overdue tickets stay in
    the existing overdue panel (not duplicated). Closed tickets are
    excluded."""

    @classmethod
    def setUpTestData(cls):
        _setup_seed()
        _enable_psa_global()
        cls.org = Organization.objects.create(name='Burn', slug='burn')
        _enable_psa_for(cls.org)
        cls.queue = Queue.objects.first()
        cls.priority = TicketPriority.objects.order_by('sort_order').first()
        cls.ttype = TicketType.objects.first()
        cls.new_status = TicketStatus.objects.filter(slug='new').first()
        cls.closed_status = (TicketStatus.objects
                             .filter(is_terminal=True).first())

        cls.user = User.objects.create_user(
            'burn-user', password='pw', email='burn@x.com', is_staff=True,
        )
        Membership.objects.create(
            user=cls.user, organization=cls.org, role=Role.OWNER, is_active=True,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        s = self.client.session
        s['2fa_prompted'] = True
        s['current_organization_id'] = self.org.id
        s.save()

    def test_in_window_open_ticket_appears_in_sla_burn(self):
        now = timezone.now()
        t = _make_ticket(
            org=self.org, priority=self.priority, status=self.new_status,
            queue=self.queue, ttype=self.ttype, subject='due in 2h',
            resolution_due_at=now + timedelta(hours=2),
        )
        resp = self.client.get('/psa/dispatch/')
        self.assertEqual(resp.status_code, 200)
        sla_burn = list(resp.context['sla_burn'])
        self.assertIn(t, sla_burn)

    def test_already_overdue_does_not_appear_in_sla_burn(self):
        # The view's overdue logic compares due-date to today via
        # `d_local < today` (date-only). Use yesterday so the ticket is
        # unambiguously overdue regardless of wall-clock hour at test time.
        now = timezone.now()
        t_overdue = _make_ticket(
            org=self.org, priority=self.priority, status=self.new_status,
            queue=self.queue, ttype=self.ttype, subject='already overdue',
            resolution_due_at=now - timedelta(days=1),
        )
        resp = self.client.get('/psa/dispatch/')
        self.assertNotIn(t_overdue, list(resp.context['sla_burn']))
        self.assertIn(t_overdue, list(resp.context['overdue']))

    def test_outside_window_does_not_appear_in_sla_burn(self):
        now = timezone.now()
        t_far = _make_ticket(
            org=self.org, priority=self.priority, status=self.new_status,
            queue=self.queue, ttype=self.ttype, subject='due in 8h',
            resolution_due_at=now + timedelta(hours=8),
        )
        resp = self.client.get('/psa/dispatch/')
        self.assertNotIn(t_far, list(resp.context['sla_burn']))

    def test_closed_ticket_does_not_appear_in_sla_burn(self):
        if self.closed_status is None:
            self.skipTest('no terminal TicketStatus in seed defaults')
        now = timezone.now()
        t_closed = _make_ticket(
            org=self.org, priority=self.priority, status=self.closed_status,
            queue=self.queue, ttype=self.ttype, subject='in window but closed',
            resolution_due_at=now + timedelta(hours=2),
        )
        resp = self.client.get('/psa/dispatch/')
        self.assertNotIn(t_closed, list(resp.context['sla_burn']))


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class DispatchBoardSortingTests(TestCase):
    """Within each lane (overdue, sla_burn, unassigned-by-day, assigned
    cells), tickets sort by `_dispatch_priority_key`. Verifies the
    higher-priority ticket lands at the head of the unassigned lane."""

    @classmethod
    def setUpTestData(cls):
        _setup_seed()
        _enable_psa_global()
        cls.org = Organization.objects.create(name='Sortlane', slug='sortlane')
        _enable_psa_for(cls.org)
        cls.queue = Queue.objects.first()
        cls.ttype = TicketType.objects.first()
        cls.new_status = TicketStatus.objects.filter(slug='new').first()
        cls.p_high = TicketPriority.objects.order_by('sort_order').first()
        cls.p_low = TicketPriority.objects.order_by('-sort_order').first()
        cls.user = User.objects.create_user(
            'sort-user', password='pw', email='sort@x.com', is_staff=True,
        )
        Membership.objects.create(
            user=cls.user, organization=cls.org, role=Role.OWNER, is_active=True,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        s = self.client.session
        s['2fa_prompted'] = True
        s['current_organization_id'] = self.org.id
        s.save()

    def test_higher_priority_unassigned_ticket_sorts_first(self):
        # Both tickets due ~24h from now — well within the 7-day window
        # but not overdue, regardless of wall-clock hour at test time.
        due = timezone.now() + timedelta(hours=24)
        t_low = _make_ticket(
            org=self.org, priority=self.p_low, status=self.new_status,
            queue=self.queue, ttype=self.ttype, subject='low',
            resolution_due_at=due,
        )
        t_high = _make_ticket(
            org=self.org, priority=self.p_high, status=self.new_status,
            queue=self.queue, ttype=self.ttype, subject='high',
            resolution_due_at=due,
        )
        resp = self.client.get('/psa/dispatch/')
        # The two unassigned tickets should land in the same day-bucket
        # within the unassigned_by_day list. Find the bucket that contains
        # both, then assert ordering.
        for lane in resp.context['unassigned_by_day']:
            lane_list = list(lane)
            if t_high in lane_list and t_low in lane_list:
                self.assertLess(lane_list.index(t_high), lane_list.index(t_low))
                return
        self.fail('expected t_high and t_low to share an unassigned-by-day bucket')
