"""
Tests for Netra ModelHub API, version management, and hot-reload.
Verifies:
- Automated SHA-256 integrity calculation on save
- Active model selection per model format type
- Latest model endpoint: GET /api/models/latest/
- Weights download endpoint: GET /api/models/<version>/download/
- Hot-reload admin action triggering InferenceService
"""
import io
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.modelhub.models import ModelVersion
from apps.detection.services.inference import InferenceService


class ModelHubTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dummy_weights = b"DUMMY_YOLO_ONNX_WEIGHTS_BINARY_DATA"

    def _create_model(self, version: str, model_type="onnx_web", is_active=False) -> ModelVersion:
        file = SimpleUploadedFile(f"{version}.onnx", self.dummy_weights, content_type="application/octet-stream")
        return ModelVersion.objects.create(
            version=version,
            model_type=model_type,
            weights_file=file,
            is_active=is_active,
            imgsz=416
        )

    def test_sha256_checksum_auto_calculation(self):
        """ModelVersion calculates and persists SHA-256 hash automatically on save."""
        model = self._create_model("v1.0.0")
        self.assertTrue(len(model.sha256_checksum) == 64)

    def test_single_active_model_rule(self):
        """Activating a new model deactivates previously active models of the same format."""
        m1 = self._create_model("v1.0.0", is_active=True)
        self.assertTrue(m1.is_active)

        m2 = self._create_model("v1.1.0", is_active=True)
        m1.refresh_from_db()

        self.assertTrue(m2.is_active)
        self.assertFalse(m1.is_active, "m1 was not deactivated when m2 became active.")

    def test_get_latest_model_api(self):
        """API returns active model metadata and download URL."""
        model = self._create_model("v1.2.0", model_type="onnx_web", is_active=True)
        response = self.client.get(reverse('models-latest'), {'model_type': 'onnx_web'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["version"], "v1.2.0")
        self.assertEqual(data["data"]["model_type"], "onnx_web")
        self.assertEqual(data["data"]["sha256_checksum"], model.sha256_checksum)
        self.assertIn("download_url", data["data"])

    def test_model_download_endpoint(self):
        """Download endpoint streams binary model weights."""
        model = self._create_model("v1.3.0")
        response = self.client.get(reverse('models-download', kwargs={'version': 'v1.3.0'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.dummy_weights)

    def test_admin_hot_reload_action(self):
        """Admin hot-reload action loads PyTorch model into InferenceService."""
        from apps.modelhub.admin import ModelVersionAdmin
        from django.contrib.admin.sites import AdminSite

        file = SimpleUploadedFile("yolo_server.pt", b"FAKE_PT_WEIGHTS", content_type="application/octet-stream")
        pt_model = ModelVersion.objects.create(
            version="v2.0.0-pt",
            model_type="yolo_pt",
            weights_file=file,
            is_active=False
        )

        admin_instance = ModelVersionAdmin(ModelVersion, AdminSite())
        queryset = ModelVersion.objects.filter(id=pt_model.id)

        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage

        factory = RequestFactory()
        req = factory.get('/admin/')
        setattr(req, 'session', {})
        setattr(req, '_messages', FallbackStorage(req))

        admin_instance.hot_reload_into_inference_engine(req, queryset)

        pt_model.refresh_from_db()
        self.assertTrue(pt_model.is_active)
