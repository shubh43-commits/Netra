"""
Models for Netra Accounts and Assistive Preferences.
Includes:
- Device: Identifies anonymous and registered phone hardware clients.
- UserSettings: Persists multimodal settings for both registered users and anonymous devices.
- EmergencyContact: Contact directory for SOS safety notifications and fall alerts.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import (
    validate_e164_phone,
    validate_speech_rate,
    validate_volume,
    validate_alert_distance,
)


class Device(models.Model):
    """
    Represents a client device identified by an anonymous or logged-in UUID.
    Permits visually impaired users to use all assistive capabilities immediately
    without an onboarding or registration barrier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
        help_text=_("Associated user if this device is authenticated.")
    )
    platform = models.CharField(
        max_length=32,
        default="web",
        choices=[("web", "Web Browser"), ("android", "Android PWA"), ("ios", "iOS Safari")]
    )
    app_version = models.CharField(max_length=32, default="1.0.0")
    analytics_opt_in = models.BooleanField(
        default=False,
        help_text=_("Explicit user opt-in required for anonymous telemetry.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["user", "last_seen"]),
        ]

    def __str__(self) -> str:
        owner = self.user.username if self.user else "Anonymous"
        return f"Device {self.id} ({owner})"

    def record_activity(self) -> None:
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])


class UserSettings(models.Model):
    """
    Assistive navigation, spatial audio, haptic, and on-device AI preferences.
    Can belong to an authenticated User OR an anonymous Device.
    """
    LANGUAGE_CHOICES = [
        ("en", _("English")),
        ("hi", _("हिन्दी (Hindi)")),
    ]

    MODEL_SIZE_CHOICES = [
        ("nano", _("YOLO Nano (Fastest, low battery)")),
        ("small", _("YOLO Small (Higher accuracy)")),
    ]

    DETECTION_MODE_CHOICES = [
        ("on_device", _("On-Device (Private, 100% offline)")),
        ("cloud", _("Cloud Assisted (Server inference & OCR)")),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="settings"
    )
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="settings"
    )

    # Audio & Voice Settings
    language = models.CharField(max_length=8, choices=LANGUAGE_CHOICES, default="en")
    speech_rate = models.FloatField(default=1.0, validators=[validate_speech_rate])
    volume = models.FloatField(default=1.0, validators=[validate_volume])
    spatial_beeps = models.BooleanField(default=True)

    # Detection & Proximity Thresholds
    alert_distance_m = models.FloatField(default=5.0, validators=[validate_alert_distance])
    vibration = models.BooleanField(default=True)

    # Battery & Motion Modes
    low_power = models.BooleanField(default=False)
    calm_mode = models.BooleanField(default=False)

    # AI Runtime
    model_size = models.CharField(max_length=16, choices=MODEL_SIZE_CHOICES, default="nano")
    detection_mode = models.CharField(max_length=16, choices=DETECTION_MODE_CHOICES, default="on_device")

    # Safety
    fall_detection_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Settings")
        verbose_name_plural = _("User Settings")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | models.Q(device__isnull=False),
                name="settings_must_belong_to_user_or_device"
            )
        ]

    def __str__(self) -> str:
        target = self.user.username if self.user else f"Device {self.device_id}"
        return f"Settings for {target} ({self.language})"


class EmergencyContact(models.Model):
    """
    Emergency contact for safety warnings, fall incidents, and motionless alerts.
    Maximum of 5 contacts per user or device.
    """
    RELATIONSHIP_CHOICES = [
        ("family", _("Family")),
        ("friend", _("Friend")),
        ("caregiver", _("Caregiver / Assistant")),
        ("medical", _("Doctor / Clinic")),
        ("other", _("Other")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="emergency_contacts"
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="emergency_contacts"
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, validators=[validate_e164_phone])
    relationship = models.CharField(max_length=32, choices=RELATIONSHIP_CHOICES, default="family")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["device", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | models.Q(device__isnull=False),
                name="contact_must_belong_to_user_or_device"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone}) - {self.relationship}"
