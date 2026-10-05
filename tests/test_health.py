"""
Integration tests for Netra System Health, Version, OpenAPI Docs, and Middlewares.
"""
import uuid
import pytest
from django.test import TestCase, Client
from django.urls import reverse


class HealthAndCoreAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        """Verify /api/health/ returns operational status."""
        response = self.client.get(reverse('api-health'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("services", data)
        self.assertIn("database", data["services"])
        self.assertEqual(data["services"]["database"], "ok")
        self.assertIn("redis", data["services"])
        self.assertIn("model_loaded", data["services"])
        self.assertEqual(data["status"], "healthy")

    def test_version_endpoint(self):
        """Verify /api/version/ returns app and API version."""
        response = self.client.get(reverse('api-version'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["app"], "Netra")
        self.assertEqual(data["api_version"], "v1")
        self.assertIn("en", data["supported_languages"])
        self.assertIn("hi", data["supported_languages"])

    def test_openapi_schema_generation(self):
        """Verify /api/schema/ generates valid OpenAPI 3 schema."""
        response = self.client.get(reverse('schema'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi", response.content.decode('utf-8'))
        self.assertIn("Netra Assistive AI API", response.content.decode('utf-8'))

    def test_swagger_ui_endpoint(self):
        """Verify /api/docs/ renders Swagger documentation."""
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger-ui", response.content.decode('utf-8'))

    def test_request_id_middleware(self):
        """Verify RequestIDMiddleware assigns and echoes correlation IDs."""
        test_uuid = str(uuid.uuid4())
        # With client-supplied ID
        response = self.client.get(reverse('api-version'), HTTP_X_REQUEST_ID=test_uuid)
        self.assertEqual(response.headers.get("X-Request-Id"), test_uuid)

        # Without client-supplied ID (auto-generated)
        response_auto = self.client.get(reverse('api-version'))
        self.assertTrue(bool(response_auto.headers.get("X-Request-Id")))

    def test_security_headers_middleware(self):
        """Verify security headers are attached to responses."""
        response = self.client.get(reverse('api-health'))
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertIn("camera=(self)", response.headers.get("Permissions-Policy", ""))
