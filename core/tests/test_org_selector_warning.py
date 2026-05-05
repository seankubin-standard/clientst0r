"""Tests for v3.17.314 — `require_organization_context` decorator now
stashes the warning state on `request` so the context processor can
surface it to templates that use plain `render()` (not TemplateResponse).
"""
from __future__ import annotations

from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path

from core.decorators import require_organization_context
from core.models import Organization


TEST_MIDDLEWARE = [
    m for m in django_settings.MIDDLEWARE
    if 'Enforce2FAMiddleware' not in m and 'AxesMiddleware' not in m
]


class OrgSelectorWarningContextTests(TestCase):
    """Verify the decorator surfaces `show_org_selector_warning` to
    templates via the request-attribute pattern (not response.context_data)."""

    def setUp(self):
        self.org_a = Organization.objects.create(name='AAA', slug='aaa')
        self.org_b = Organization.objects.create(name='BBB', slug='bbb')
        self.staff = User.objects.create_user(
            'staff', 'staff@x.com', 'pw', is_staff=True, is_superuser=True,
        )

    def test_decorator_sets_request_attrs_on_global_view(self):
        """When a staff user has no org context, the decorator stashes
        `_show_org_selector_warning` and `_available_organizations` on
        the request before calling the view."""
        rf = RequestFactory()
        captured = {}

        @require_organization_context
        def probe(request):
            captured['show'] = getattr(request, '_show_org_selector_warning',
                                          None)
            captured['orgs'] = getattr(request, '_available_organizations',
                                          None)
            return HttpResponse('ok')

        req = rf.get('/x/')
        req.user = self.staff
        req.is_staff_user = True
        req.current_organization = None
        # No `current_organization_id` in session → middleware-style global view
        from django.contrib.sessions.backends.base import SessionBase
        req.session = SessionBase()

        # Patch get_request_organization to return None for the test
        from unittest import mock
        with mock.patch('core.middleware.get_request_organization',
                        return_value=None):
            probe(req)
        self.assertTrue(captured['show'])
        self.assertEqual(
            sorted(o.name for o in captured['orgs']),
            ['AAA', 'BBB'],
        )

    def test_decorator_skips_request_attrs_when_org_present(self):
        """When the user has an org context, the warning attrs aren't
        set — the form renders normally."""
        rf = RequestFactory()
        captured = {}

        @require_organization_context
        def probe(request):
            captured['show'] = getattr(request, '_show_org_selector_warning',
                                          None)
            return HttpResponse('ok')

        req = rf.get('/x/')
        req.user = self.staff
        req.is_staff_user = True
        req.current_organization = self.org_a

        from unittest import mock
        with mock.patch('core.middleware.get_request_organization',
                        return_value=self.org_a):
            probe(req)
        # Attribute never set → getattr returns None
        self.assertIsNone(captured['show'])

    def test_context_processor_surfaces_request_attrs(self):
        """The `organization_context` context processor reads the
        request flags and surfaces them to every template."""
        from core.context_processors import organization_context
        rf = RequestFactory()
        req = rf.get('/x/')
        req.user = self.staff
        req.is_staff_user = True
        req.current_organization = None
        # Simulate decorator having run
        req._show_org_selector_warning = True
        req._available_organizations = [self.org_a, self.org_b]

        ctx = organization_context(req)
        self.assertTrue(ctx['show_org_selector_warning'])
        self.assertEqual(len(ctx['available_organizations']), 2)

    def test_context_processor_defaults_when_attrs_missing(self):
        """A regular request without the decorator running has
        `show_org_selector_warning=False` and an empty list."""
        from core.context_processors import organization_context
        rf = RequestFactory()
        req = rf.get('/x/')
        req.user = self.staff
        req.is_staff_user = True
        req.current_organization = self.org_a

        ctx = organization_context(req)
        self.assertFalse(ctx['show_org_selector_warning'])
        self.assertEqual(ctx['available_organizations'], [])
