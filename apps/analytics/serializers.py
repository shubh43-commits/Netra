"""
Serializers for Netra Telemetry Events and Safety Incidents.
"""
from rest_framework import serializers
from .models import UsageEvent, SafetyIncident


class UsageEventSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(max_length=64, required=False)

    class Meta:
        model = UsageEvent
        fields = ['id', 'device_id', 'event_type', 'event_data', 'timestamp']
        read_only_fields = ['id']


class UsageEventBatchSerializer(serializers.Serializer):
    events = UsageEventSerializer(many=True, required=False)
    # Also support submitting a single event directly
    event_type = serializers.CharField(required=False)
    event_data = serializers.DictField(required=False, default=dict)
    device_id = serializers.CharField(required=False)


class SafetyIncidentCreateSerializer(serializers.Serializer):
    incident_type = serializers.ChoiceField(
        choices=SafetyIncident.INCIDENT_TYPE_CHOICES,
        default='fall_detected'
    )
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    device_id = serializers.CharField(max_length=64, required=False)


class EmergencyLinkSerializer(serializers.Serializer):
    contact_name = serializers.CharField()
    contact_phone = serializers.CharField()
    message = serializers.CharField()
    whatsapp_url = serializers.CharField()
    sms_url = serializers.CharField()


class SafetyIncidentResponseSerializer(serializers.Serializer):
    incident_id = serializers.UUIDField()
    incident_type = serializers.CharField()
    created_at = serializers.DateTimeField()
    emergency_contacts = EmergencyLinkSerializer(many=True)
