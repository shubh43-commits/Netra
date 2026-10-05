"""
Tests for Netra Telemetry Events and Celery Background Jobs.
Verifies:
- Bulk telemetry recording (POST /api/events/)
- User privacy opt-in / opt-out enforcement
- 90-day feedback purge background task
- 30-day analytics aggregation and raw data purge task
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Device, UserSettings
from apps.feedback.models import DetectionReport
from apps.analytics.models import UsageEvent, DailyAnalyticsSummary
from apps.analytics.tasks import purge_expired_feedback_reports, aggregate_daily_usage_metrics

User = get_user_model()


class AnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.device = Device.objects.create(analytics_opt_in=True)
        self.dev_id = str(self.device.id)
        self.settings = UserSettings.objects.create(device=self.device)

    def test_record_batch_events_success(self):
        """Batch of navigation telemetry events is recorded."""
        payload = {
            "events": [
                {
                    "event_type": "session_start",
                    "event_data": {"mode": "cloud_ws"}
                },
                {
                    "event_type": "hazard_detected",
                    "event_data": {"class_name": "car", "distance_m": 2.5}
                }
            ],
            "device_id": self.dev_id
        }
        response = self.client.post(
            reverse('record-events'),
            payload,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["success"])
        self.assertEqual(UsageEvent.objects.filter(device_id=self.dev_id).count(), 2)

    def test_privacy_opt_out_skips_recording(self):
        """When user disables analytics, events are silently discarded per privacy mandate."""
        self.device.analytics_opt_in = False
        self.device.save()

        payload = {
            "event_type": "session_start",
            "event_data": {},
            "device_id": self.dev_id
        }
        response = self.client.post(
            reverse('record-events'),
            payload,
            content_type="application/json",
            HTTP_X_DEVICE_ID=self.dev_id
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("privacy", response.json()["message"].lower())
        self.assertEqual(UsageEvent.objects.filter(device_id=self.dev_id).count(), 0)

    def test_feedback_retention_purge_task(self):
        """Celery job purges DetectionReport frames older than 90 days."""
        now = timezone.now()
        # 1. Fresh report (10 days old)
        fresh_file = SimpleUploadedFile("fresh.jpg", b"JPG_DATA", content_type="image/jpeg")
        r_fresh = DetectionReport.objects.create(device_id="dev1", image=fresh_file)

        # 2. Expired report (95 days old)
        old_file = SimpleUploadedFile("old.jpg", b"JPG_DATA", content_type="image/jpeg")
        r_old = DetectionReport.objects.create(device_id="dev2", image=old_file)
        DetectionReport.objects.filter(id=r_old.id).update(created_at=now - timedelta(days=95))

        purged_count = purge_expired_feedback_reports()
        self.assertEqual(purged_count, 1)

        self.assertTrue(DetectionReport.objects.filter(id=r_fresh.id).exists())
        self.assertFalse(DetectionReport.objects.filter(id=r_old.id).exists())

    def test_daily_analytics_aggregation_task(self):
        """Celery task aggregates daily sessions and purges raw events older than 30 days."""
        yesterday = (timezone.now() - timedelta(days=1)).date()
        dt = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()) + timedelta(hours=12))

        # Create sample events yesterday
        e1 = UsageEvent.objects.create(device_id="dev_a", event_type="session_start", timestamp=dt)
        e2 = UsageEvent.objects.create(device_id="dev_a", event_type="hazard_detected", timestamp=dt)
        e3 = UsageEvent.objects.create(device_id="dev_b", event_type="session_end", event_data={"fps": 12.0}, timestamp=dt)

        # Create ancient event (40 days old)
        e_old = UsageEvent.objects.create(device_id="dev_old", event_type="session_start", timestamp=timezone.now() - timedelta(days=40))

        result = aggregate_daily_usage_metrics(str(yesterday))
        self.assertEqual(result['total_sessions'], 1)
        self.assertEqual(result['total_hazards'], 1)
        self.assertEqual(result['unique_devices'], 2)

        # Verify summary row was created
        summary = DailyAnalyticsSummary.objects.get(date=yesterday)
        self.assertEqual(summary.total_sessions, 1)
        self.assertEqual(summary.total_hazards_detected, 1)

        # Verify 40-day old raw event was purged
        self.assertFalse(UsageEvent.objects.filter(id=e_old.id).exists())
