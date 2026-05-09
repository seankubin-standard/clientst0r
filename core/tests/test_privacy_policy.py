"""
Tests for `/privacy-policy/` (v3.17.447). Public, anonymous-accessible
HTML page rendered from `docs/PRIVACY_POLICY.md` so Play Console + Apple
App Store reviewers can verify the privacy URL without an account.
"""
from django.conf import settings as django_settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse


TEST_MIDDLEWARE = [
    m for m in django_settings.MIDDLEWARE
    if 'Enforce2FAMiddleware' not in m and 'AxesMiddleware' not in m
]


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE, SECURE_SSL_REDIRECT=False)
class PrivacyPolicyViewTests(TestCase):

    def test_anonymous_user_gets_200(self):
        """Reviewer / random visitor with no session should see the page."""
        resp = Client().get('/privacy-policy/')
        self.assertEqual(resp.status_code, 200)

    def test_url_resolves_via_reverse(self):
        """Named URL resolves so other code can `reverse('privacy_policy')`."""
        self.assertEqual(reverse('privacy_policy'), '/privacy-policy/')

    def test_renders_markdown_to_html(self):
        """The MD source becomes real HTML (heading + body present)."""
        resp = Client().get('/privacy-policy/')
        body = resp.content.decode('utf-8')
        # H1 from the markdown rendered as <h1>
        self.assertIn('<h1>Privacy Policy', body)
        # A representative phrase from the policy body
        self.assertIn('self-hosted', body.lower())

    def test_response_is_html(self):
        resp = Client().get('/privacy-policy/')
        self.assertIn('text/html', resp['Content-Type'])
