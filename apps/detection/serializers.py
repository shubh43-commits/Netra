"""
Serializers for Netra Computer Vision, Scene Description, and OCR Endpoints.
"""
from typing import Dict, Any
from rest_framework import serializers
from PIL import Image

MAX_UPLOAD_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.FileField(required=True)
    language = serializers.ChoiceField(choices=["en", "hi"], default="en", required=False)
    imgsz = serializers.IntegerField(default=416, required=False, min_value=160, max_value=1280)

    def validate_image(self, value):
        if value.size > MAX_UPLOAD_IMAGE_BYTES:
            raise serializers.ValidationError("Image file size must not exceed 2 MB.")

        # Verify image integrity with Pillow
        try:
            value.seek(0)
            img = Image.open(value)
            img.verify()
            value.seek(0)
        except Exception:
            raise serializers.ValidationError("Uploaded file is corrupted or not a valid image.")

        return value


class DetectionItemSerializer(serializers.Serializer):
    class_name = serializers.CharField()
    confidence = serializers.FloatField()
    box = serializers.ListField(child=serializers.FloatField(), min_length=4, max_length=4)
    direction = serializers.CharField()
    distance_m = serializers.FloatField()
    approaching = serializers.BooleanField(default=False)
    priority_score = serializers.FloatField(required=False)


class DetectResponseSerializer(serializers.Serializer):
    items = DetectionItemSerializer(many=True)
    top = DetectionItemSerializer(many=True)
    count = serializers.IntegerField()
    latency_ms = serializers.FloatField()


class DescribeResponseSerializer(serializers.Serializer):
    text = serializers.CharField()
    items = DetectionItemSerializer(many=True)
    language = serializers.CharField()
    latency_ms = serializers.FloatField()


class OCRBlockSerializer(serializers.Serializer):
    text = serializers.CharField()
    confidence = serializers.FloatField()
    box = serializers.ListField(child=serializers.FloatField(), min_length=4, max_length=4)
    direction = serializers.CharField()


class OCRResponseSerializer(serializers.Serializer):
    blocks = OCRBlockSerializer(many=True)
    count = serializers.IntegerField()
    combined_text = serializers.CharField()
    latency_ms = serializers.FloatField()
