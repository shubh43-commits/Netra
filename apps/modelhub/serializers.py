"""
Serializers for Netra ModelHub versions.
"""
from rest_framework import serializers
from .models import ModelVersion


class ModelVersionSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ModelVersion
        fields = [
            'version',
            'model_type',
            'download_url',
            'sha256_checksum',
            'min_app_version',
            'imgsz',
            'is_active',
            'release_notes',
            'uploaded_at'
        ]

    def get_download_url(self, obj) -> str:
        request = self.context.get('request')
        if obj.weights_file:
            if request:
                return request.build_absolute_uri(obj.weights_file.url)
            return obj.weights_file.url
        return ""
