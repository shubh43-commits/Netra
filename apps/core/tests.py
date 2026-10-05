"""
Tests for Netra Core Views, PWA Endpoints, and Internationalization (Stage 1).
"""
from django.test import TestCase, Client
from django.urls import reverse


class NetraStage1CoreTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_renders_with_exact_design(self):
        """Test home page loads with HTTP 200 and required design elements."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Check brand and title
        self.assertIn("netra", content)
        self.assertIn("Your phone just got", content)
        self.assertIn("eyes.", content)

        # Check skip link and accessibility
        self.assertIn('class="skip"', content)
        self.assertIn('aria-label="Main"', content)
        self.assertIn('id="alert"', content)
        self.assertIn('id="perf"', content)

        # Check static asset links
        self.assertIn('/static/css/netra.css', content)
        self.assertIn('/static/vendor/three.min.js', content)
        self.assertIn('/static/js/hero3d.js', content)
        self.assertIn('/static/js/home.js', content)

    def test_navigate_placeholder_view(self):
        """Test navigate view route and template."""
        response = self.client.get(reverse('navigate'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'navigate.html')
        self.assertIn("Live", response.content.decode('utf-8'))

    def test_demo_placeholder_view(self):
        """Test demo view route and template."""
        response = self.client.get(reverse('demo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'demo.html')
        self.assertIn("Simulated", response.content.decode('utf-8'))

    def test_offline_page_view(self):
        """Test offline fallback view route and template."""
        response = self.client.get(reverse('offline'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'offline.html')
        self.assertIn("offline", response.content.decode('utf-8'))

    def test_service_worker_root_endpoint(self):
        """Test /sw.js endpoint with required PWA header."""
        response = self.client.get(reverse('service_worker_root'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Service-Worker-Allowed'), '/')
        self.assertIn('application/javascript', response.headers.get('Content-Type'))
        self.assertIn('netra-shell-v1', response.content.decode('utf-8'))

    def test_manifest_endpoint(self):
        """Test /manifest.webmanifest endpoint with valid JSON content type."""
        response = self.client.get(reverse('manifest_root'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/manifest+json', response.headers.get('Content-Type'))
        manifest_data = response.json()
        self.assertEqual(manifest_data.get('short_name'), 'Netra')
        self.assertEqual(manifest_data.get('theme_color'), '#f5efe6')

    def test_hindi_internationalization(self):
        """Test Hindi translation rendering."""
        # Switch language to Hindi
        response = self.client.post(reverse('set_language'), {'language': 'hi'})
        self.assertEqual(response.status_code, 302)

        # Request home page with hindi session/cookie
        response_hi = self.client.get(reverse('home'))
        content_hi = response_hi.content.decode('utf-8')
        self.assertIn("नेत्र", content_hi)
        self.assertIn("नज़र", content_hi)
        self.assertIn("चलना शुरू करें", content_hi)
