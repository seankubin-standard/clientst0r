"""
Reports tests — Phase 3.1.

Cover the canonical query layer (`reports.queries`) and the new
Profitability-by-Client report view (URL gate, HTML render, CSV export).
"""
from django.conf import settings as django_settings
from django.test import TestCase, override_settings


# Strip the project-wide 2FA enforcement + Axes middleware so the test
# client can hit the views directly. Same pattern as `psa/tests.py`.
TEST_MIDDLEWARE = [
    m for m in django_settings.MIDDLEWARE
    if 'Enforce2FAMiddleware' not in m and 'AxesMiddleware' not in m
]


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class ProfitabilityQueryTests(TestCase):
    """v3.17.139: canonical queries return correct shape and totals."""

    def setUp(self):
        from datetime import date, timedelta
        from django.contrib.auth.models import User
        from core.models import Organization
        from psa.models import (
            Queue, TicketStatus, TicketPriority, TicketType, Ticket,
            TicketTimeEntry, Invoice,
        )
        from django.core.management import call_command
        call_command('psa_seed_defaults', verbosity=0)
        self.org = Organization.objects.create(name='Profit Co', slug='profit-co')
        self.user = User.objects.create_user('alice', 'a@x.com', 'pw')
        self.t = Ticket.objects.create(
            organization=self.org, subject='X',
            queue=Queue.objects.first(),
            status=TicketStatus.objects.filter(slug='new').first(),
            priority=TicketPriority.objects.first(),
            ticket_type=TicketType.objects.first(),
        )
        self.today = date.today()
        TicketTimeEntry.objects.create(
            ticket=self.t, user=self.user,
            started_at=self.today, duration_minutes=120, is_billable=True,
        )
        Invoice.objects.create(
            organization=self.org, client_org=self.org,
            invoice_number='INV-2026-1', title='Test',
            invoice_date=self.today, due_date=self.today,
            total=500, amount_paid=200,
            status='partial', subtotal=500, tax_amount=0, currency='USD',
        )

    def test_hours_minutes_by_client(self):
        from reports.queries import hours_minutes_by_client
        rows = hours_minutes_by_client(self.today, self.today)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['billable_minutes'], 120)
        self.assertEqual(rows[0]['client_id'], self.org.id)

    def test_revenue_by_client(self):
        from reports.queries import revenue_by_client
        rows = revenue_by_client(self.today, self.today)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['invoiced'], 500.0)
        self.assertEqual(rows[0]['outstanding'], 300.0)

    def test_profitability_combines(self):
        from reports.queries import profitability_by_client
        rows = profitability_by_client(self.today, self.today, default_loaded_rate=60)
        self.assertEqual(len(rows), 1)
        # 2h × $60 = $120 cost; revenue $500; margin $380; pct 76%
        self.assertAlmostEqual(rows[0]['cost'], 120.0, places=1)
        self.assertAlmostEqual(rows[0]['margin'], 380.0, places=1)
        self.assertAlmostEqual(rows[0]['margin_pct'], 76.0, places=1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class ProfitabilityReportViewTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user('admin1', 'a@x.com', 'pw',
                                              is_staff=True, is_superuser=True)
        self.regular = User.objects.create_user('reg', 'r@x.com', 'pw')

    def test_staff_can_view(self):
        self.client.force_login(self.staff)
        r = self.client.get('/reports/psa/profitability-by-client/')
        self.assertEqual(r.status_code, 200)

    def test_non_staff_redirected(self):
        self.client.force_login(self.regular)
        r = self.client.get('/reports/psa/profitability-by-client/')
        self.assertIn(r.status_code, [302, 403])

    def test_csv_export(self):
        self.client.force_login(self.staff)
        r = self.client.get('/reports/psa/profitability-by-client/?format=csv')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'].split(';')[0].strip(), 'text/csv')
        self.assertIn(b'Client', r.content)  # header row


# ---------------------------------------------------------------------------
# Phase 3.2 — TechCostRate + per-tech / contract / project profitability
# ---------------------------------------------------------------------------

class TechCostRateTests(TestCase):
    def test_rate_for_returns_default_when_no_rows(self):
        from datetime import date
        from django.contrib.auth.models import User
        from resourcing.models import TechCostRate
        from reports.queries import DEFAULT_LOADED_RATE
        u = User.objects.create_user('alice', 'a@x.com', 'pw')
        self.assertEqual(TechCostRate.rate_for(u, date.today()),
                         DEFAULT_LOADED_RATE)

    def test_rate_for_picks_most_recent_effective(self):
        from datetime import date
        from decimal import Decimal
        from django.contrib.auth.models import User
        from resourcing.models import TechCostRate
        u = User.objects.create_user('alice', 'a@x.com', 'pw')
        TechCostRate.objects.create(user=u, rate_per_hour=Decimal('50'),
                                    effective_from=date(2024, 1, 1))
        TechCostRate.objects.create(user=u, rate_per_hour=Decimal('70'),
                                    effective_from=date(2025, 6, 1))
        self.assertEqual(TechCostRate.rate_for(u, date(2025, 7, 1)),
                         Decimal('70'))
        self.assertEqual(TechCostRate.rate_for(u, date(2024, 6, 1)),
                         Decimal('50'))

    def test_rate_for_ignores_future_effective(self):
        from datetime import date
        from decimal import Decimal
        from django.contrib.auth.models import User
        from resourcing.models import TechCostRate
        from reports.queries import DEFAULT_LOADED_RATE
        u = User.objects.create_user('alice', 'a@x.com', 'pw')
        TechCostRate.objects.create(user=u, rate_per_hour=Decimal('99'),
                                    effective_from=date(2030, 1, 1))
        # Today < 2030, so falls back to default
        self.assertEqual(TechCostRate.rate_for(u, date(2026, 1, 1)),
                         DEFAULT_LOADED_RATE)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class ProfitabilityByTechTests(TestCase):
    """Phase 3.2 — per-tech profitability uses TechCostRate."""

    def setUp(self):
        from datetime import date
        from decimal import Decimal
        from django.contrib.auth.models import User
        from django.core.management import call_command
        from core.models import Organization
        from psa.models import (
            Queue, TicketStatus, TicketPriority, TicketType, Ticket,
            TicketTimeEntry, Invoice,
        )
        from resourcing.models import TechCostRate
        call_command('psa_seed_defaults', verbosity=0)
        self.org = Organization.objects.create(name='ProfitTechCo', slug='profit-tech-co')
        self.user = User.objects.create_user('alice', 'a@x.com', 'pw')
        self.t = Ticket.objects.create(
            organization=self.org, subject='X',
            queue=Queue.objects.first(),
            status=TicketStatus.objects.filter(slug='new').first(),
            priority=TicketPriority.objects.first(),
            ticket_type=TicketType.objects.first(),
        )
        self.today = date.today()
        TicketTimeEntry.objects.create(
            ticket=self.t, user=self.user,
            started_at=self.today, duration_minutes=120, is_billable=True,
        )
        Invoice.objects.create(
            organization=self.org, client_org=self.org,
            invoice_number='INV-2026-T1', title='TestTech',
            invoice_date=self.today, due_date=self.today,
            total=300, amount_paid=0, status='sent',
            subtotal=300, tax_amount=0, currency='USD',
        )
        # Custom cost rate $50/hr
        TechCostRate.objects.create(user=self.user, rate_per_hour=Decimal('50'),
                                    effective_from=self.today)

    def test_per_tech_uses_cost_rate(self):
        from reports.queries import profitability_by_tech
        rows = profitability_by_tech(self.today, self.today)
        self.assertEqual(len(rows), 1)
        # 2 hours × $50/hr = $100 cost
        self.assertAlmostEqual(rows[0]['cost'], 100.0, places=1)
        self.assertEqual(rows[0]['tech_username'], 'alice')

    def test_cost_estimate_by_client_uses_per_tech_rate(self):
        from reports.queries import cost_estimate_by_client
        rows = cost_estimate_by_client(self.today, self.today)
        self.assertEqual(len(rows), 1)
        # 2h × $50 = $100 (not 2h × $60 placeholder)
        self.assertAlmostEqual(rows[0]['cost'], 100.0, places=1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class ProfitabilityByContractTests(TestCase):
    """Phase 3.2 — per-contract grouping via Contract.for_ticket."""

    def setUp(self):
        from datetime import date, timedelta
        from decimal import Decimal
        from django.contrib.auth.models import User
        from django.core.management import call_command
        from core.models import Organization
        from psa.models import (
            Queue, TicketStatus, TicketPriority, TicketType, Ticket,
            TicketTimeEntry, Contract, Invoice,
        )
        call_command('psa_seed_defaults', verbosity=0)
        self.msp = Organization.objects.create(name='MSPInc', slug='msp-inc')
        self.client_org = Organization.objects.create(name='ClientCo', slug='client-co')
        self.user = User.objects.create_user('alice', 'a@x.com', 'pw')
        self.today = date.today()
        self.contract = Contract.objects.create(
            organization=self.msp, client_org=self.client_org,
            name='Block 50', contract_type='block_hours', status='active',
            start_date=self.today - timedelta(days=30),
            end_date=self.today + timedelta(days=30),
            total_hours=Decimal('50'), hourly_rate=Decimal('150'),
        )
        self.t = Ticket.objects.create(
            organization=self.client_org, subject='X',
            queue=Queue.objects.first(),
            status=TicketStatus.objects.filter(slug='new').first(),
            priority=TicketPriority.objects.first(),
            ticket_type=TicketType.objects.first(),
        )
        TicketTimeEntry.objects.create(
            ticket=self.t, user=self.user,
            started_at=self.today, duration_minutes=60, is_billable=True,
        )
        Invoice.objects.create(
            organization=self.msp, client_org=self.client_org,
            source_contract=self.contract,
            invoice_number='INV-2026-C1', title='Contract billing',
            invoice_date=self.today, due_date=self.today,
            total=Decimal('500'), amount_paid=0, status='sent',
            subtotal=Decimal('500'), tax_amount=0, currency='USD',
        )

    def test_aggregates_per_contract(self):
        from reports.queries import profitability_by_contract
        rows = profitability_by_contract(self.today, self.today)
        # We expect at least one row matching our contract
        match = [r for r in rows if r['contract_id'] == self.contract.id]
        self.assertEqual(len(match), 1)
        r = match[0]
        self.assertEqual(r['client_name'], 'ClientCo')
        # Revenue includes the $500 invoice
        self.assertGreaterEqual(r['revenue'], 500.0)
        # Cost = 1h × default $60 = $60
        self.assertAlmostEqual(r['cost'], 60.0, places=1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class ProfitabilityByProjectTests(TestCase):
    """Phase 3.2 — per-project grouping via Ticket.project."""

    def setUp(self):
        from datetime import date
        from decimal import Decimal
        from django.contrib.auth.models import User
        from django.core.management import call_command
        from core.models import Organization
        from psa.models import (
            Queue, TicketStatus, TicketPriority, TicketType, Ticket,
            TicketTimeEntry, Project, Invoice,
        )
        call_command('psa_seed_defaults', verbosity=0)
        self.msp = Organization.objects.create(name='MSPInc', slug='msp-inc-2')
        self.client_org = Organization.objects.create(name='ProjClient', slug='proj-client')
        self.user = User.objects.create_user('alice', 'a@x.com', 'pw')
        self.today = date.today()
        self.project = Project.objects.create(
            organization=self.msp, client_org=self.client_org,
            name='Migration', status='active',
        )
        self.t = Ticket.objects.create(
            organization=self.client_org, subject='Migration ticket',
            queue=Queue.objects.first(),
            status=TicketStatus.objects.filter(slug='new').first(),
            priority=TicketPriority.objects.first(),
            ticket_type=TicketType.objects.first(),
            project=self.project,
        )
        TicketTimeEntry.objects.create(
            ticket=self.t, user=self.user,
            started_at=self.today, duration_minutes=180, is_billable=True,
        )
        Invoice.objects.create(
            organization=self.msp, client_org=self.client_org,
            source_ticket=self.t,
            invoice_number='INV-2026-P1', title='Project billing',
            invoice_date=self.today, due_date=self.today,
            total=Decimal('900'), amount_paid=0, status='sent',
            subtotal=Decimal('900'), tax_amount=0, currency='USD',
        )

    def test_aggregates_per_project(self):
        from reports.queries import profitability_by_project
        rows = profitability_by_project(self.today, self.today)
        match = [r for r in rows if r['project_id'] == self.project.id]
        self.assertEqual(len(match), 1)
        r = match[0]
        self.assertEqual(r['project_name'], 'Migration')
        self.assertAlmostEqual(r['revenue'], 900.0, places=1)
        # 3h × $60 default = $180
        self.assertAlmostEqual(r['cost'], 180.0, places=1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class ProfitabilityPivotViewTests(TestCase):
    """Phase 3.2 — staff can hit the three new HTML/CSV report views."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user('admin1', 'a@x.com', 'pw',
                                              is_staff=True, is_superuser=True)
        self.regular = User.objects.create_user('reg', 'r@x.com', 'pw')

    def test_by_tech_view_staff_html(self):
        self.client.force_login(self.staff)
        r = self.client.get('/reports/psa/profitability-by-tech/')
        self.assertEqual(r.status_code, 200)

    def test_by_tech_view_csv(self):
        self.client.force_login(self.staff)
        r = self.client.get('/reports/psa/profitability-by-tech/?format=csv')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'].split(';')[0].strip(), 'text/csv')
        self.assertIn(b'Tech', r.content)

    def test_by_contract_view_staff_html(self):
        self.client.force_login(self.staff)
        r = self.client.get('/reports/psa/profitability-by-contract/')
        self.assertEqual(r.status_code, 200)

    def test_by_project_view_staff_html(self):
        self.client.force_login(self.staff)
        r = self.client.get('/reports/psa/profitability-by-project/')
        self.assertEqual(r.status_code, 200)

    def test_by_tech_non_staff_redirected(self):
        self.client.force_login(self.regular)
        r = self.client.get('/reports/psa/profitability-by-tech/')
        self.assertIn(r.status_code, [302, 403])
