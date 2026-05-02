"""Tests for Phase 39 compliance evidence packs."""
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings


TEST_MIDDLEWARE = [
    m for m in django_settings.MIDDLEWARE
    if 'Enforce2FAMiddleware' not in m and 'AxesMiddleware' not in m
]


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class EvidencePackTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        from accounts.models import Membership, Role
        from core.models import Organization
        cls.org_a = Organization.objects.create(name='OrgA', slug='cep-a')
        cls.org_b = Organization.objects.create(name='OrgB', slug='cep-b')
        cls.owner_a = User.objects.create_user('cep-owner-a', 'a@x.com', 'pw',
                                                first_name='AOwner')
        cls.owner_b = User.objects.create_user('cep-owner-b', 'b@x.com', 'pw',
                                                first_name='BOwner')
        cls.staff = User.objects.create_user('cep-staff', 's@x.com', 'pw',
                                              is_superuser=True, is_staff=True)
        Membership.objects.create(user=cls.owner_a, organization=cls.org_a,
                                  role=Role.OWNER, is_active=True)
        Membership.objects.create(user=cls.owner_b, organization=cls.org_b,
                                  role=Role.OWNER, is_active=True)

    def _login(self, c, user, org=None):
        c.force_login(user)
        s = c.session
        s['2fa_prompted'] = True
        if org is not None:
            s['current_organization_id'] = org.id
        s.save()

    def test_owner_gets_200_html_with_org_name(self):
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'OrgA')
        self.assertContains(r, 'Two-Factor Authentication Status')
        self.assertContains(r, 'User Access Report')
        self.assertContains(r, 'Password Access History')
        self.assertContains(r, 'Asset Inventory')
        self.assertContains(r, 'Ticket / SLA History')
        # v3.17.226 — Phase 39 v2 sections
        self.assertContains(r, 'SSL / Domain Expiration')
        self.assertContains(r, 'Uptime Evidence')
        self.assertContains(r, 'Vulnerability Summary')
        self.assertContains(r, 'Backup Evidence')

    def test_owner_gets_200_zip(self):
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/?format=zip')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/zip')
        self.assertIn('attachment', r['Content-Disposition'])
        import io
        import json
        import zipfile
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        names = zf.namelist()
        self.assertIn('manifest.json', names)
        for section in ('two_factor', 'user_access', 'password_history',
                        'asset_inventory', 'ticket_sla',
                        'ssl_domain', 'uptime', 'vulnerabilities', 'backups'):
            self.assertIn(f'{section}.csv', names)
        manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
        self.assertEqual(manifest['organization'], 'OrgA')
        self.assertEqual(len(manifest['sections']), 9)

    def test_other_org_owner_gets_404(self):
        c = Client()
        self._login(c, self.owner_b, self.org_b)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertEqual(r.status_code, 404)

    def test_anonymous_redirected_to_login(self):
        c = Client()
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertIn(r.status_code, [302, 401])

    def test_superuser_can_access_any_org(self):
        c = Client()
        self._login(c, self.staff, self.org_b)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'OrgA')

    def test_missing_org_returns_404(self):
        c = Client()
        self._login(c, self.staff)
        r = c.get('/compliance/organizations/99999/evidence-pack/')
        self.assertEqual(r.status_code, 404)

    def test_tenant_scope_user_access(self):
        # OrgB has owner_b; that user must NOT show in OrgA's pack.
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'cep-owner-b')

    def test_tenant_scope_assets(self):
        from assets.models import Asset
        Asset.objects.create(organization=self.org_b, name='OrgBSerialUnique',
                             asset_type='other', serial_number='B-SECRET-SN-12345')
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertNotContains(r, 'B-SECRET-SN-12345')

    def test_tenant_scope_password_history(self):
        from audit.models import AuditLog
        AuditLog.log(
            user=self.owner_b, action='read',
            organization=self.org_b,
            object_type='password', object_id=99,
            object_repr='Cross-tenant secret name',
            description='reveal',
        )
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertNotContains(r, 'Cross-tenant secret name')

    def test_v226_sections_tenant_scoped(self):
        # v3.17.226: SSL/uptime + vuln sections are tenant-scoped.
        # Create OrgB-only WebsiteMonitor + SecurityAlert; verify they
        # do not leak into OrgA's pack.
        from monitoring.models import WebsiteMonitor
        from security_alerts.models import SecurityAlert, SecurityVendorConnection
        WebsiteMonitor.objects.create(
            organization=self.org_b, name='OrgB-Monitor-XYZ',
            url='https://orgb.example.com',
        )
        conn = SecurityVendorConnection.objects.create(
            organization=self.org_b, name='OrgB Vendor',
            provider='huntress', category='edr',
            base_url='https://example.invalid/', is_active=True,
        )
        SecurityAlert.objects.create(
            connection=conn, organization=self.org_b, client_org=self.org_b,
            external_id='orgb-vuln-1',
            title='OrgB-only-CVE-99999',
            severity='critical', status='new',
        )
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'OrgB-Monitor-XYZ')
        self.assertNotContains(r, 'OrgB-only-CVE-99999')

    def test_audit_log_written_on_generate(self):
        from audit.models import AuditLog
        before = AuditLog.objects.filter(
            organization=self.org_a,
            object_type='compliance.EvidencePack',
        ).count()
        c = Client()
        self._login(c, self.owner_a, self.org_a)
        r = c.get(f'/compliance/organizations/{self.org_a.id}/evidence-pack/')
        self.assertEqual(r.status_code, 200)
        after = AuditLog.objects.filter(
            organization=self.org_a,
            object_type='compliance.EvidencePack',
        ).count()
        self.assertEqual(after, before + 1)
