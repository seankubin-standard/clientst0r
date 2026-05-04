"""
Tests for Phase 12 / v3.17.244: only superusers can access settings + change feature toggles.

Audit guarantees:
  * Every `core/settings_views.py` view is gated `@user_passes_test(is_superuser)`.
  * The PSA global settings view (which mutates `SystemSetting` feature
    toggles) is also superuser-only — was previously
    `is_superuser OR is_staff_user` (now tightened).
  * Non-superuser staff users get 404 on either, never a writable form.
"""
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings


TEST_MIDDLEWARE = [
    m for m in django_settings.MIDDLEWARE
    if 'Enforce2FAMiddleware' not in m and 'AxesMiddleware' not in m
]


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class SettingsAccessControlTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        from accounts.models import UserProfile
        from core.models import SystemSetting
        s = SystemSetting.get_settings()
        s.psa_enabled = True
        s.save()
        cls.superuser = User.objects.create_user(
            'su', 'su@x.com', 'pw', is_superuser=True, is_staff=True,
        )
        cls.staff_user = User.objects.create_user('staff', 'st@x.com', 'pw')
        # Mark as MSP staff via UserProfile.user_type if the column exists.
        profile, _ = UserProfile.objects.get_or_create(user=cls.staff_user)
        if hasattr(profile, 'user_type'):
            profile.user_type = 'staff'
            profile.save(update_fields=['user_type'])
        cls.regular_user = User.objects.create_user('regular', 'r@x.com', 'pw')

    def _login(self, c, user):
        c.force_login(user)
        s = c.session
        s['2fa_prompted'] = True
        s.save()

    # --- core/settings_views.py — already correct, verify guards hold ----

    def test_settings_general_blocked_for_non_superuser(self):
        c = Client()
        self._login(c, self.regular_user)
        r = c.get('/core/settings/general/')
        # @user_passes_test default behavior is redirect to login.
        self.assertIn(r.status_code, [302, 403])

    def test_settings_features_blocked_for_non_superuser(self):
        c = Client()
        self._login(c, self.regular_user)
        r = c.get('/core/settings/features/')
        self.assertIn(r.status_code, [302, 403])

    def test_settings_general_works_for_superuser(self):
        c = Client()
        self._login(c, self.superuser)
        r = c.get('/core/settings/general/')
        self.assertEqual(r.status_code, 200)

    def test_settings_features_works_for_superuser(self):
        c = Client()
        self._login(c, self.superuser)
        r = c.get('/core/settings/features/')
        self.assertEqual(r.status_code, 200)

    # --- PSA global settings — tightened in v3.17.244 --------------------

    def test_psa_global_settings_blocked_for_staff_user(self):
        # Pre-v3.17.244 this would have returned 200 (staff_user was
        # allowed in). After tightening, only superusers pass.
        c = Client()
        self._login(c, self.staff_user)
        r = c.get('/psa/settings/')
        self.assertEqual(r.status_code, 404)

    def test_psa_global_settings_blocked_for_regular_user(self):
        c = Client()
        self._login(c, self.regular_user)
        r = c.get('/psa/settings/')
        self.assertEqual(r.status_code, 404)

    def test_psa_global_settings_works_for_superuser(self):
        c = Client()
        self._login(c, self.superuser)
        r = c.get('/psa/settings/')
        self.assertEqual(r.status_code, 200)

    def test_staff_user_cannot_post_psa_feature_toggle(self):
        # Tries to flip psa_csat_enabled on via the PSA settings POST.
        # Must 404, and SystemSetting must be unchanged.
        from core.models import SystemSetting
        before = SystemSetting.get_settings().psa_csat_enabled
        c = Client()
        self._login(c, self.staff_user)
        r = c.post('/psa/settings/', data={
            'action': 'save_globals',
            'psa_csat_enabled': 'on',
            'psa_portal_enabled': 'on',
        })
        self.assertEqual(r.status_code, 404)
        after = SystemSetting.get_settings().psa_csat_enabled
        self.assertEqual(before, after)
