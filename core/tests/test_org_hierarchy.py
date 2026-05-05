"""Tests for Phase 18 — Multi-Location Client Hierarchy (v3.17.240)."""
from django.test import TestCase

from core.models import Organization
from core.utils import descendant_org_ids


class OrgHierarchyHelperTests(TestCase):
    """`descendant_org_ids` walks the parent chain correctly."""

    @classmethod
    def setUpTestData(cls):
        cls.acme = Organization.objects.create(name='ACME Corp', slug='acme')
        cls.east = Organization.objects.create(
            name='ACME East', slug='acme-east', parent=cls.acme,
        )
        cls.west = Organization.objects.create(
            name='ACME West', slug='acme-west', parent=cls.acme,
        )
        cls.east_a = Organization.objects.create(
            name='ACME East — Boston', slug='acme-east-bos', parent=cls.east,
        )
        cls.unrelated = Organization.objects.create(name='Other Co', slug='other')

    def test_descendant_ids_for_top_level_includes_all_children(self):
        ids = descendant_org_ids(self.acme)
        self.assertIn(self.acme.pk, ids)
        self.assertIn(self.east.pk, ids)
        self.assertIn(self.west.pk, ids)
        self.assertIn(self.east_a.pk, ids)
        self.assertNotIn(self.unrelated.pk, ids)

    def test_descendant_ids_for_leaf_returns_only_self(self):
        ids = descendant_org_ids(self.east_a)
        self.assertEqual(ids, {self.east_a.pk})

    def test_descendant_ids_handles_none(self):
        self.assertEqual(descendant_org_ids(None), set())

    def test_ancestors_property_walks_up(self):
        chain = [a.pk for a in self.east_a.ancestors]
        self.assertEqual(chain, [self.east.pk, self.acme.pk])

    def test_breadcrumb_label_renders_chain(self):
        self.assertEqual(
            self.east_a.breadcrumb_label,
            'ACME Corp → ACME East → ACME East — Boston',
        )


class OrgHierarchyManagerTests(TestCase):
    """`OrganizationManager.for_organization()` follows parent chain."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = Organization.objects.create(name='Parent', slug='ph-p')
        cls.child = Organization.objects.create(
            name='Child', slug='ph-c', parent=cls.parent,
        )
        cls.unrelated = Organization.objects.create(name='Stranger', slug='ph-s')

    def test_for_organization_inherits_descendants_by_default(self):
        from assets.models import Asset
        a_parent = Asset.objects.create(
            organization=self.parent, name='Parent Asset', asset_type='other',
        )
        a_child = Asset.objects.create(
            organization=self.child, name='Child Asset', asset_type='other',
        )
        a_other = Asset.objects.create(
            organization=self.unrelated, name='Other Asset', asset_type='other',
        )
        names = set(
            Asset.objects.for_organization(self.parent)
                          .values_list('name', flat=True)
        )
        self.assertEqual(names, {'Parent Asset', 'Child Asset'})
        self.assertNotIn('Other Asset', names)

    def test_for_organization_with_strict_skips_descendants(self):
        from assets.models import Asset
        Asset.objects.create(
            organization=self.parent, name='Parent only', asset_type='other',
        )
        Asset.objects.create(
            organization=self.child, name='Child', asset_type='other',
        )
        names = set(
            Asset.objects.for_organization(self.parent, include_descendants=False)
                          .values_list('name', flat=True)
        )
        self.assertEqual(names, {'Parent only'})

    def test_child_query_does_not_see_parent_rows(self):
        from assets.models import Asset
        Asset.objects.create(
            organization=self.parent, name='Parent secret', asset_type='other',
        )
        names = set(
            Asset.objects.for_organization(self.child)
                          .values_list('name', flat=True)
        )
        self.assertNotIn('Parent secret', names)


class SharedInfrastructureTests(TestCase):
    """v3.17.252 — Phase 18 v2: descendants see ancestors' shared assets."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = Organization.objects.create(name='Holding', slug='hi-p')
        cls.child = Organization.objects.create(
            name='Subsidiary', slug='hi-c', parent=cls.parent,
        )
        cls.unrelated = Organization.objects.create(name='Unrelated', slug='hi-u')

    def test_visible_to_org_includes_shared_ancestor(self):
        from assets.models import Asset
        # Parent owns a shared asset (is_shared_with_descendants=True)
        shared = Asset.objects.create(
            organization=self.parent, name='Shared switch',
            asset_type='other', is_shared_with_descendants=True,
        )
        # Parent owns a private asset
        private = Asset.objects.create(
            organization=self.parent, name='Parent only switch',
            asset_type='other', is_shared_with_descendants=False,
        )
        # Child owns its own
        own = Asset.objects.create(
            organization=self.child, name='Child server',
            asset_type='other',
        )
        names = set(Asset.visible_to_org(self.child).values_list('name', flat=True))
        self.assertIn('Shared switch', names)
        self.assertIn('Child server', names)
        self.assertNotIn('Parent only switch', names)

    def test_visible_to_org_for_parent_returns_own_plus_descendants(self):
        from assets.models import Asset
        Asset.objects.create(
            organization=self.parent, name='Parent asset', asset_type='other',
        )
        Asset.objects.create(
            organization=self.child, name='Child asset', asset_type='other',
        )
        # Parent sees both via descendant inheritance from v3.17.240.
        names = set(Asset.visible_to_org(self.parent).values_list('name', flat=True))
        self.assertEqual(names, {'Parent asset', 'Child asset'})

    def test_visible_to_org_does_not_include_unrelated_org(self):
        from assets.models import Asset
        Asset.objects.create(
            organization=self.unrelated, name='Stranger asset',
            asset_type='other', is_shared_with_descendants=True,
        )
        # Unrelated org's shared asset must NOT bleed into our hierarchy.
        names = set(Asset.visible_to_org(self.child).values_list('name', flat=True))
        self.assertNotIn('Stranger asset', names)


class OrgFormParentValidationTests(TestCase):
    """Form prevents picking yourself or a descendant as parent."""

    @classmethod
    def setUpTestData(cls):
        cls.a = Organization.objects.create(name='A', slug='form-a')
        cls.b = Organization.objects.create(name='B', slug='form-b', parent=cls.a)
        cls.c = Organization.objects.create(name='C', slug='form-c', parent=cls.b)
        cls.unrelated = Organization.objects.create(name='U', slug='form-u')

    def test_form_excludes_self_and_descendants_from_parent_choices(self):
        from accounts.forms import OrganizationForm
        form = OrganizationForm(instance=self.a)
        choices = list(form.fields['parent'].queryset.values_list('pk', flat=True))
        self.assertNotIn(self.a.pk, choices)
        self.assertNotIn(self.b.pk, choices)
        self.assertNotIn(self.c.pk, choices)
        self.assertIn(self.unrelated.pk, choices)


class SiteSLAOverrideTests(TestCase):
    """Phase 18 v7 (v3.17.282): per-priority SLA overrides on Organization
    walk up the parent chain so a child site falls back to its parent's
    overrides, then to whatever the contract / queue defaults are."""

    @classmethod
    def setUpTestData(cls):
        cls.parent = Organization.objects.create(
            name='HQ', slug='sla-hq',
            sla_overrides={
                'P1': {'response_minutes': 15, 'resolution_minutes': 240},
            },
        )
        cls.child_with_own = Organization.objects.create(
            name='Site-A', slug='sla-a', parent=cls.parent,
            sla_overrides={
                'P1': {'response_minutes': 5, 'resolution_minutes': 120},
            },
        )
        cls.child_inherit = Organization.objects.create(
            name='Site-B', slug='sla-b', parent=cls.parent,
        )
        cls.standalone = Organization.objects.create(name='Standalone',
                                                      slug='sla-standalone')

    def test_own_override_used_first(self):
        ov = self.child_with_own.sla_override_for('P1')
        self.assertEqual(ov['response_minutes'], 5)

    def test_falls_back_to_parent(self):
        ov = self.child_inherit.sla_override_for('P1')
        self.assertEqual(ov['response_minutes'], 15)

    def test_no_override_returns_none(self):
        self.assertIsNone(self.standalone.sla_override_for('P1'))
        self.assertIsNone(self.child_inherit.sla_override_for('P5'))

    def test_empty_priority_code_returns_none(self):
        self.assertIsNone(self.parent.sla_override_for(''))


class RegionTaggingTests(TestCase):
    """Phase 18 v9 (v3.17.282): `Organization.region` + `normalized_region`."""

    def test_normalized_strips_and_lowercases(self):
        org = Organization.objects.create(name='A', slug='reg-a',
                                            region=' EMEA ')
        self.assertEqual(org.normalized_region, 'emea')

    def test_blank_region_normalizes_to_empty(self):
        org = Organization.objects.create(name='B', slug='reg-b')
        self.assertEqual(org.normalized_region, '')
