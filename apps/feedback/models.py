"""
Models for Netra Feedback and Wrong Detection Reporting.
Stores:
- User-flagged frames and false-alarm reports with randomized secure UUID paths
- Bounding box annotations and telemetry metadata for dataset retraining
- 90-day retention indicator
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


def report_image_path(instance, filename: str) -> str:
    """Generate a randomized, unguessable UUID storage path for feedback frames."""
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        ext = 'jpg'
    return f"reports/{uuid.uuid4().hex}.{ext}"


class DetectionReport(models.Model):
    """
    User-submitted bug and misclassification reports containing camera frame
    and optional user annotations for AI model retraining.
    """
    ISSUE_CHOICES = [
        ('missed_obstacle', 'Missed Obstacle (Did not detect hazard)'),
        ('false_alarm', 'False Alarm (Detected phantom obstacle)'),
        ('wrong_distance', 'Incorrect Distance Estimation'),
        ('wrong_label', 'Misclassified Object Name'),
        ('other', 'Other Issue / Feedback'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_reports'
    )
    device_id = models.CharField(max_length=64, db_index=True)
    image = models.ImageField(upload_to=report_image_path)
    issue_type = models.CharField(max_length=32, choices=ISSUE_CHOICES, default='missed_obstacle')
    user_note = models.TextField(blank=True, default='')
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Telemetry including detected bounding boxes, client app version, and sensor data."
    )
    is_reviewed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Detection Report'
        verbose_name_plural = 'Detection Reports'

    def __str__(self) -> str:
        return f"Report {str(self.id)[:8]} - {self.get_issue_type_display()} ({self.device_id[:8]})"

    @property
    def is_expired(self) -> bool:
        """Indicates if report has exceeded 90-day privacy retention threshold."""
        return (timezone.now() - self.created_at).days > 90
