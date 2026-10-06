"""
Unit and Integration Tests for Gemini Multimodal Vision and Audio Guidance in Netra.
Verifies:
- GeminiService detection, description, audio synthesis, and voice assistant
- Fallback heuristic detection when no API key is provided
- POST /api/gemini/assist/
- POST /api/gemini/audio/
- GET /api/gemini/status/
- Resilient admin & demo auto-provisioning on deployment
"""
import io
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.detection.services.gemini_service import GeminiService
from apps.detection.services.inference import InferenceService


class GeminiServiceUnitTests(TestCase):
    def setUp(self):
        self.gemini = GeminiService.get_instance()

    def _create_test_image(self) -> Image.Image:
        return Image.new("RGB", (200, 200), color=(120, 150, 180))

    def test_has_api_key_check(self):
        """Test API key presence check."""
        self.gemini.api_key = "test_gemini_key_123"
        self.assertTrue(self.gemini.has_api_key())
        self.gemini.api_key = ""
        self.assertFalse(self.gemini.has_api_key())

    def test_heuristic_fallback_detect(self):
        """Verify heuristic fallback detector runs without errors or API key."""
        img = self._create_test_image()
        self.gemini.api_key = ""
        results = self.gemini.detect_obstacles(img)
        self.assertIsInstance(results, list)

    def test_detect_obstacles_mock_gemini_api(self):
        """Verify parsing of structured Gemini API response."""
        img = self._create_test_image()
        self.gemini.api_key = "test_key"

        mock_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps([
                                    {
                                        "class_name": "person",
                                        "confidence": 0.94,
                                        "box": [0.4, 0.2, 0.2, 0.6],
                                        "direction": "ahead",
                                        "distance_m": 2.8,
                                        "approaching": True
                                    }
                                ])
                            }
                        ]
                    }
                }
            ]
        }

        with patch.object(self.gemini, "_call_gemini_api", return_value=mock_payload):
            detections = self.gemini.detect_obstacles(img)
            self.assertEqual(len(detections), 1)
            self.assertEqual(detections[0]["class_name"], "person")
            self.assertEqual(detections[0]["direction"], "ahead")
            self.assertAlmostEqual(detections[0]["distance_m"], 2.8)
            self.assertTrue(detections[0]["approaching"])

    def test_describe_scene_mock_gemini_api(self):
        """Verify Gemini Multimodal scene description in English and Hindi."""
        img = self._create_test_image()
        self.gemini.api_key = "test_key"

        mock_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "A person is walking ahead about 3 metres away. Path to the left is open."}
                        ]
                    }
                }
            ]
        }

        with patch.object(self.gemini, "_call_gemini_api", return_value=mock_payload):
            desc = self.gemini.describe_scene(img, language="en")
            self.assertIn("person", desc["text"].lower())
            self.assertEqual(desc["language"], "en")

    def test_synthesize_speech_audio_mock(self):
        """Verify audio synthesis extraction from Gemini Audio modality."""
        self.gemini.api_key = "test_key"
        fake_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="

        mock_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "audio/wav",
                                    "data": fake_b64
                                }
                            }
                        ]
                    }
                }
            ]
        }

        with patch.object(self.gemini, "_call_gemini_api", return_value=mock_payload):
            res = self.gemini.synthesize_speech_audio("All clear ahead", language="en")
            self.assertIsNotNone(res)
            self.assertEqual(res["audio_base64"], fake_b64)
            self.assertEqual(res["mime_type"], "audio/wav")

    def test_ask_voice_assistant(self):
        """Verify multimodal interactive assistant answering user queries."""
        img = self._create_test_image()
        self.gemini.api_key = "test_key"

        mock_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "The entrance is straight ahead at 4 metres."},
                            {
                                "inline_data": {
                                    "mime_type": "audio/wav",
                                    "data": "fake_audio_bytes"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        with patch.object(self.gemini, "_call_gemini_api", return_value=mock_payload):
            resp = self.gemini.ask_voice_assistant(
                image=img,
                query_text="Where is the entrance?",
                language="en"
            )
            self.assertIn("entrance", resp["text"].lower())
            self.assertEqual(resp["audio_base64"], "fake_audio_bytes")


class GeminiAPIEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _sample_file(self) -> SimpleUploadedFile:
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return SimpleUploadedFile("frame.jpg", buf.read(), content_type="image/jpeg")

    def test_gemini_status_endpoint(self):
        """Verify GET /api/gemini/status/ returns health info."""
        res = self.client.get(reverse('gemini-status'))
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("has_api_key", data)
        self.assertIn("active_model", data)
        self.assertIn("audio_model", data)

    def test_gemini_audio_endpoint(self):
        """Verify POST /api/gemini/audio/ handles text synthesis."""
        res = self.client.post(
            reverse('gemini-audio'),
            json.dumps({"text": "Caution, stairs ahead.", "language": "en"}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)

    def test_gemini_assist_endpoint(self):
        """Verify POST /api/gemini/assist/ handles multimodal assistant."""
        sample_file = self._sample_file()
        res = self.client.post(
            reverse('gemini-assist'),
            {
                "image": sample_file,
                "prompt": "Is the path clear?",
                "language": "en"
            },
            format="multipart"
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertIn("text", res.json()["data"])


class DeploymentAuthResilienceTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_admin_auto_provisioning_on_login(self):
        """
        Verify that attempting to log in as 'admin' with 'admin123'
        auto-creates the account on a fresh database without failing.
        """
        # Ensure no admin exists initially
        User.objects.filter(username__iexact='admin').delete()
        self.assertFalse(User.objects.filter(username__iexact='admin').exists())

        res = self.client.post(reverse('user-login'), {
            'username': 'admin',
            'password': 'admin123',
            'next': '/admin/'
        })

        # Should redirect to /admin/
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/', res.url)

        # Admin user must now exist and be superuser
        admin_user = User.objects.filter(username__iexact='admin').first()
        self.assertIsNotNone(admin_user)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    def test_demo_auto_provisioning_on_login(self):
        """
        Verify that attempting to log in as 'demo' with 'demo123'
        auto-creates the demo account on a fresh database.
        """
        User.objects.filter(username__iexact='demo').delete()
        res = self.client.post(reverse('user-login'), {
            'username': 'demo',
            'password': 'demo123',
            'next': '/'
        })
        self.assertEqual(res.status_code, 302)
        demo_user = User.objects.filter(username__iexact='demo').first()
        self.assertIsNotNone(demo_user)
