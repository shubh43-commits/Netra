"""
Unit and Integration Tests for Netra Detection, Proximity, Priority, and Natural Description.
"""
import io
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.detection.services.constants import REAL_WORLD_HEIGHTS_M
from apps.detection.services.inference import InferenceService
from apps.detection.services.priority import calculate_hazard_score, select_top_hazards
from apps.detection.services.tracker import StreamTracker
from apps.detection.services.describe import describe_scene


class DetectionServiceUnitTests(TestCase):
    def setUp(self):
        self.inference = InferenceService.get_instance()

    def test_distance_estimation(self):
        """Verify monocular distance formula based on real-world heights."""
        # Person height is 1.7m. If normalized box height is 0.5:
        # distance = (1.7 * 1.0) / 0.5 = 3.4m
        dist_person = self.inference.estimate_distance("person", 0.5)
        self.assertAlmostEqual(dist_person, 3.4, delta=0.1)

        # Car height is 1.5m. If box height is 0.25:
        # distance = (1.5 * 1.0) / 0.25 = 6.0m
        dist_car = self.inference.estimate_distance("car", 0.25)
        self.assertAlmostEqual(dist_car, 6.0, delta=0.1)

        # Clamping at minimum distance (0.3m)
        dist_close = self.inference.estimate_distance("person", 1.0)
        self.assertGreaterEqual(dist_close, 0.3)

    def test_direction_classification(self):
        """Verify direction binning for left (<0.33), ahead (0.33-0.66), and right (>0.66)."""
        # Center at 0.15 (left)
        self.assertEqual(self.inference.classify_direction(0.1, 0.1), "left")

        # Center at 0.50 (ahead)
        self.assertEqual(self.inference.classify_direction(0.4, 0.2), "ahead")

        # Center at 0.85 (right)
        self.assertEqual(self.inference.classify_direction(0.8, 0.1), "right")

    def test_priority_ranking_and_approach_weight(self):
        """
        Verify that dangerous approaching hazards take priority over distant or peripheral items.
        """
        car_ahead_close = {
            "class_name": "car",
            "distance_m": 2.0,
            "direction": "ahead",
            "approaching": True,
            "confidence": 0.95,
        }
        bench_right_far = {
            "class_name": "bench",
            "distance_m": 8.0,
            "direction": "right",
            "approaching": False,
            "confidence": 0.80,
        }
        stairs_close = {
            "class_name": "stairs",
            "distance_m": 1.5,
            "direction": "ahead",
            "approaching": False,
            "confidence": 0.90,
        }

        score_car = calculate_hazard_score(car_ahead_close)
        score_bench = calculate_hazard_score(bench_right_far)
        score_stairs = calculate_hazard_score(stairs_close)

        self.assertGreater(score_car, score_bench)
        self.assertGreater(score_stairs, score_bench)

        # select_top_hazards should return top 2
        items = [bench_right_far, car_ahead_close, stairs_close]
        top = select_top_hazards(items, limit=2)
        self.assertEqual(len(top), 2)
        top_classes = [t["class_name"] for t in top]
        self.assertIn("car", top_classes)
        self.assertIn("stairs", top_classes)

    def test_stream_tracker_approach_detection(self):
        """Verify IoU tracker detects approaching motion across frames."""
        tracker = StreamTracker()

        # Frame 1: Person at distance 5m, small box
        frame1 = [{
            "class_name": "person",
            "box": [0.45, 0.40, 0.10, 0.20],
            "distance_m": 5.0,
        }]
        res1 = tracker.update(frame1)
        self.assertFalse(res1[0]["approaching"])

        # Frame 2: Same person gets closer (3.5m) and box expands
        frame2 = [{
            "class_name": "person",
            "box": [0.43, 0.35, 0.14, 0.30],
            "distance_m": 3.5,
        }]
        res2 = tracker.update(frame2)
        self.assertTrue(res2[0]["approaching"])
        self.assertEqual(res2[0]["track_id"], res1[0]["track_id"])

    def test_scene_description_english_and_hindi(self):
        """Verify natural language scene narration templates."""
        # Empty scene
        empty_en = describe_scene([], language="en")
        self.assertIn("All clear ahead", empty_en["text"])

        empty_hi = describe_scene([], language="hi")
        self.assertIn("आगे रास्ता साफ़ है", empty_hi["text"])

        # Scene with person ahead and car left
        items = [
            {"class_name": "person", "distance_m": 3.0, "direction": "ahead", "approaching": False, "confidence": 0.9},
            {"class_name": "car", "distance_m": 6.0, "direction": "left", "approaching": True, "confidence": 0.95},
        ]

        desc_en = describe_scene(items, language="en")
        self.assertIn("person", desc_en["text"].lower())
        self.assertIn("car", desc_en["text"].lower())
        self.assertIn("ahead", desc_en["text"])

        desc_hi = describe_scene(items, language="hi")
        self.assertIn("व्यक्ति", desc_hi["text"])
        self.assertIn("गाड़ी", desc_hi["text"])


class DetectionAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        # Setup mock model on InferenceService for rapid and deterministic API tests
        self.inference = InferenceService.get_instance()
        self.inference.set_mock_model(lambda img: [
            {
                "class_name": "person",
                "confidence": 0.92,
                "box": [0.42, 0.30, 0.15, 0.40],
                "direction": "ahead",
                "distance_m": 4.25,
                "approaching": False
            },
            {
                "class_name": "car",
                "confidence": 0.88,
                "box": [0.10, 0.40, 0.20, 0.25],
                "direction": "left",
                "distance_m": 6.0,
                "approaching": True
            }
        ])

    def tearDown(self):
        self.inference._mock_inference_func = None

    def _create_sample_jpeg_file(self, width: int = 100, height: int = 100) -> SimpleUploadedFile:
        img = Image.new("RGB", (width, height), color=(200, 100, 50))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return SimpleUploadedFile("test.jpg", buffer.read(), content_type="image/jpeg")

    def test_post_detect_endpoint(self):
        """Verify /api/detect/ processes image upload and returns structured items."""
        sample_file = self._create_sample_jpeg_file()
        response = self.client.post(
            reverse('detect'),
            {"image": sample_file},
            format="multipart"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["count"], 2)
        self.assertEqual(len(data["data"]["top"]), 2)
        self.assertIn("latency_ms", data["data"])

    def test_post_describe_endpoint(self):
        """Verify /api/describe/ returns localized scene description text."""
        sample_file = self._create_sample_jpeg_file()
        response = self.client.post(
            reverse('describe'),
            {"image": sample_file, "language": "hi"},
            format="multipart"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["language"], "hi")
        self.assertIn("व्यक्ति", data["data"]["text"])

    def test_oversized_image_rejected(self):
        """Verify uploads > 2 MB are rejected."""
        # 2.5 MB fake content
        large_bytes = b"\xff\xd8\xff" + (b"0" * (int(2.5 * 1024 * 1024)))
        large_file = SimpleUploadedFile("big.jpg", large_bytes, content_type="image/jpeg")
        response = self.client.post(
            reverse('detect'),
            {"image": large_file},
            format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("2 MB", str(response.json()))
