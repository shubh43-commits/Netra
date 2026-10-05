"""
API Views for Netra Telemetry Events and Safety Incidents.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.utils import api_response
from apps.accounts.models import UserSettings, EmergencyContact, Device
from .models import UsageEvent, SafetyIncident
from .serializers import (
    UsageEventBatchSerializer,
    SafetyIncidentCreateSerializer,
    SafetyIncidentResponseSerializer,
)


class RecordEventsView(APIView):
    """
    Records opt-in telemetry metrics from navigation sessions.
    Respects user privacy: strictly discarded if analytics_opt_in is disabled.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Record Telemetry Events (Batch)",
        description="Records anonymous usage events (session start/end, hazard alerts). Ignored if user has disabled analytics.",
        request=UsageEventBatchSerializer,
        responses={
            201: OpenApiResponse(description="Events recorded"),
            200: OpenApiResponse(description="Telemetry ignored per user privacy setting"),
        },
        tags=["Analytics"]
    )
    def post(self, request, *args, **kwargs) -> Response:
        serializer = UsageEventBatchSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                success=False,
                message="Invalid telemetry payload.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        device_id = data.get('device_id') or request.headers.get('X-Device-ID') or 'anonymous'
        user = request.user if request.user.is_authenticated else None

        # Privacy Check: Verify if analytics opt-in is enabled
        opt_in = True
        if user:
            dev = user.devices.filter(analytics_opt_in=True).first()
            if not dev and user.devices.exists():
                opt_in = False
        else:
            dev_obj = None
            try:
                dev_obj = Device.objects.filter(id=device_id).first()
            except Exception:
                pass
            if dev_obj:
                opt_in = dev_obj.analytics_opt_in

        if not opt_in:
            return api_response(
                success=True,
                message="Telemetry skipped per user privacy preferences.",
                status_code=status.HTTP_200_OK
            )

        # Build events list
        raw_events = data.get('events', [])
        # If single event provided at top-level
        if not raw_events and data.get('event_type'):
            raw_events = [{
                'event_type': data.get('event_type'),
                'event_data': data.get('event_data', {}),
                'device_id': device_id
            }]

        events_to_create = []
        for ev in raw_events:
            ev_type = ev.get('event_type')
            if not ev_type:
                continue
            events_to_create.append(
                UsageEvent(
                    device_id=ev.get('device_id') or device_id,
                    user=user,
                    event_type=ev_type,
                    event_data=ev.get('event_data', {})
                )
            )

        if events_to_create:
            UsageEvent.objects.bulk_create(events_to_create)

        return api_response(
            success=True,
            message=f"Recorded {len(events_to_create)} telemetry event(s).",
            status_code=status.HTTP_201_CREATED
        )


class ReportSafetyIncidentView(APIView):
    """
    Reports an urgent safety incident (fall detected, panic button, inactivity).
    Generates ready-to-open WhatsApp and SMS alert links with GPS location for registered contacts.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Report Safety Incident (Fall Detection / Panic)",
        description="Logs a critical incident and returns pre-formatted WhatsApp and SMS links with GPS coordinates for emergency contacts.",
        request=SafetyIncidentCreateSerializer,
        responses={201: SafetyIncidentResponseSerializer},
        tags=["Analytics"]
    )
    def post(self, request, *args, **kwargs) -> Response:
        serializer = SafetyIncidentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                success=False,
                message="Invalid incident payload.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        device_id = data.get('device_id') or request.headers.get('X-Device-ID') or 'anonymous'
        user = request.user if request.user.is_authenticated else None

        incident = SafetyIncident.objects.create(
            device_id=device_id,
            user=user,
            incident_type=data.get('incident_type', 'fall_detected'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )

        # Retrieve registered emergency contacts
        contacts = []
        if user:
            contacts = list(EmergencyContact.objects.filter(user=user))
        if not contacts:
            try:
                contacts = list(EmergencyContact.objects.filter(device__id=device_id))
            except Exception:
                contacts = []

        # Generate pre-filled contact links
        contact_links = []
        for c in contacts:
            contact_links.append(
                incident.generate_emergency_links(
                    contact_phone=c.phone,
                    contact_name=c.name
                )
            )

        return api_response(
            success=True,
            message="Safety incident logged. Emergency contact links generated.",
            data={
                "incident_id": str(incident.id),
                "incident_type": incident.incident_type,
                "created_at": incident.created_at.isoformat(),
                "emergency_contacts": contact_links
            },
            status_code=status.HTTP_201_CREATED
        )
