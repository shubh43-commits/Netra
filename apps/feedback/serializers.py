"""
Serializers for Netra User Feedback and Misclassification Reports.
"""
from rest_framework import serializers
from PIL import Image

from .models import DetectionReport

MAX_REPORT_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB limit for reports


class DetectionReportSerializer(serializers.ModelSerializer):
    """
    Serializes bug report submissions from both authenticated users and anonymous devices.
    """
    image = serializers.FileField(required=True)
    device_id = serializers.CharField(max_length=64, required=False)

    class Meta:
        model = DetectionReport
        fields = [
            'id',
            'device_id',
            'image',
            'issue_type',
            'user_note',
            'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_image(self, value):
        if value.size > MAX_REPORT_IMAGE_BYTES:
            raise serializers.ValidationError("Report image file must not exceed 5 MB.")

        try:
            value.seek(0)
            img = Image.open(value)
            img.verify()
            value.seek(0)
        except Exception:
            raise serializers.ValidationError("Uploaded file is corrupted or not a valid image format.")

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None

        # Resolve device ID from validated data, request header, or default
        device_id = validated_data.get('device_id')
        if not device_id and request:
            device_id = request.headers.get('X-Device-ID')
        if not device_id:
            device_id = 'anonymous'

        validated_data['user'] = user
        validated_data['device_id'] = device_id

        return super().create(validated_data)
