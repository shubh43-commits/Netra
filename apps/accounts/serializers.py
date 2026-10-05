"""
Serializers for Netra Accounts, Authentication, and Settings API.
"""
from typing import Dict, Any
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Device, UserSettings, EmergencyContact
from .validators import validate_e164_phone


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "platform", "app_version", "analytics_opt_in", "created_at", "last_seen"]
        read_only_fields = ["created_at", "last_seen"]


class DeviceRegistrationSerializer(serializers.Serializer):
    device_id = serializers.UUIDField(required=False)
    platform = serializers.ChoiceField(
        choices=["web", "android", "ios"],
        default="web",
        required=False
    )
    app_version = serializers.CharField(max_length=32, default="1.0.0", required=False)
    analytics_opt_in = serializers.BooleanField(default=False, required=False)


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            "language",
            "speech_rate",
            "volume",
            "spatial_beeps",
            "alert_distance_m",
            "vibration",
            "low_power",
            "calm_mode",
            "model_size",
            "detection_mode",
            "fall_detection_enabled",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class EmergencyContactSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[validate_e164_phone])

    class Meta:
        model = EmergencyContact
        fields = ["id", "name", "phone", "relationship", "created_at"]
        read_only_fields = ["id", "created_at"]

    def to_internal_value(self, data):
        if isinstance(data, dict) and "phone_number" in data and "phone" not in data:
            data = data.copy()
            data["phone"] = data["phone_number"]
        return super().to_internal_value(data)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        request = self.context.get("request")
        if request and not self.instance:
            user = request.user if request.user.is_authenticated else None
            device = getattr(request, "device", None)
            if not user and not device:
                from .services import get_or_create_device
                device_id = getattr(request, "device_id", None) or request.headers.get("X-Device-Id")
                if device_id:
                    device, _ = get_or_create_device(device_id)
                    request.device = device

            count = 0
            if user:
                count = EmergencyContact.objects.filter(user=user).count()
            elif device:
                count = EmergencyContact.objects.filter(device=device).count()

            if count >= 5:
                raise serializers.ValidationError(
                    "A maximum of 5 emergency contacts is permitted."
                )

        return attrs


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, min_length=3)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    device_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.UUIDField(required=False, allow_null=True)


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True, help_text="Optional refresh token to blacklist")


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserPublicSerializer()
    merged_from_device = serializers.BooleanField(default=False)
