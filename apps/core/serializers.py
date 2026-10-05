"""
Serializers for Netra Core API endpoints.
"""
from rest_framework import serializers


class HealthCheckServiceStatusSerializer(serializers.Serializer):
    database = serializers.CharField()
    redis = serializers.CharField()
    model_loaded = serializers.BooleanField()


class HealthCheckResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    services = HealthCheckServiceStatusSerializer()
    environment = serializers.CharField()
    timestamp = serializers.IntegerField()
    version = serializers.CharField()


class VersionResponseSerializer(serializers.Serializer):
    app = serializers.CharField()
    tagline = serializers.CharField()
    version = serializers.CharField()
    api_version = serializers.CharField()
    supported_languages = serializers.ListField(child=serializers.CharField())
    docs_url = serializers.CharField()
    offline_url = serializers.CharField()
