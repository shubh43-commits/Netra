"""
Tests for Netra Detection Feedback and Dataset Export.
Verifies:
- Bug and false-alarm report submission with image
- File size limit guard (5 MB)
- User / Device ID attribution
- Admin YOLO dataset ZIP packaging
"""
import io
import zipfile
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.feedback.models import DetectionReport

User = get_user_model()


class FeedbackAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="reporter", password="password123")

    def _create_dummy_image(self, size=(100, 100), color="red") -> SimpleUploadedFile:
        buf = io.BytesIO()
        img = Image.new("RGB", size, color=color)
        img.save(buf, format="JPEG")
        return SimpleUploadedFile("frame.jpg", buf.getvalue(), content_type="image/jpeg")

    def test_anonymous_report_submission(self):
        """Anonymous user can submit false-alarm report with device ID header."""
        img_file = self._create_dummy_image()
        response = self.client.post(
            reverse('feedback-report'),
            {
                "image": img_file,
                "issue_type": "false_alarm",
                "user_note": "A fire hydrant was misdetected as a child.",
                "device_id": "test_dev_report_01"
            },
            HTTP_X_DEVICE_ID="test_dev_report_01"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("report_id", data["data"])

        report = DetectionReport.objects.get(id=data["data"]["report_id"])
        self.assertEqual(report.device_id, "test_dev_report_01")
        self.assertEqual(report.issue_type, "false_alarm")
        self.assertIsNone(report.user)

    def test_authenticated_user_report_submission(self):
        """Logged in user submission is linked to user account."""
        self.client.force_login(self.user)
        img_file = self._create_dummy_image()
        response = self.client.post(
            reverse('feedback-report'),
            {
                "image": img_file,
                "issue_type": "missed_obstacle",
                "user_note": "Did not see stairs.",
            }
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        report = DetectionReport.objects.get(id=data["data"]["report_id"])
        self.assertEqual(report.user, self.user)

    def test_oversized_report_image_rejected(self):
        """Uploads exceeding 5 MB limit are rejected with 400 Bad Request."""
        large_bytes = b"\xff\xd8\xff" + (b"0" * (int(5.5 * 1024 * 1024)))
        large_file = SimpleUploadedFile("huge.jpg", large_bytes, content_type="image/jpeg")
        response = self.client.post(
            reverse('feedback-report'),
            {"image": large_file, "issue_type": "other"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("5 MB", str(response.json()))

    def test_admin_yolo_dataset_export(self):
        """Verify export action generates a valid YOLO dataset ZIP archive."""
        from apps.feedback.admin import DetectionReportAdmin
        from django.contrib.admin.sites import AdminSite

        img_file = self._create_dummy_image()
        report = DetectionReport.objects.create(
            device_id="admin_test_dev",
            image=img_file,
            issue_type="missed_obstacle",
            metadata={"boxes": [{"class_name": "stairs", "box": [0.5, 0.5, 0.3, 0.4]}]}
        )

        admin_instance = DetectionReportAdmin(DetectionReport, AdminSite())
        queryset = DetectionReport.objects.filter(id=report.id)
        response = admin_instance.export_as_yolo_dataset(None, queryset)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        # Inspect ZIP content in memory
        zip_buf = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buf, 'r') as zf:
            namelist = zf.namelist()
            self.assertIn('data.yaml', namelist)
            yaml_content = zf.read('data.yaml').decode('utf-8')
            self.assertIn('names:', yaml_content)

            # Check images and labels folders
            img_files = [n for n in namelist if n.startswith('images/')]
            lbl_files = [n for n in namelist if n.startswith('labels/')]
            self.assertEqual(len(img_files), 1)
            self.assertEqual(len(lbl_files), 1)

            # Validate label content format
            label_text = zf.read(lbl_files[0]).decode('utf-8')
            parts = label_text.strip().split()
            self.assertEqual(len(parts), 5)  # class_idx cx cy w h
