"""
Django Admin integration for Netra Analytics, Telemetry, and Safety Incidents.
Provides:
- High-level telemetry cards
- Incident tracking with map links
- Pre-aggregated daily summaries
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum

from .models import UsageEvent, DailyAnalyticsSummary, SafetyIncident


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'device_id_short', 'user', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('device_id', 'user__username')
    readonly_fields = ('id', 'timestamp')

    def device_id_short(self, obj) -> str:
        return f"{obj.device_id[:12]}..."
    device_id_short.short_description = "Device ID"


@admin.register(SafetyIncident)
class SafetyIncidentAdmin(admin.ModelAdmin):
    list_display = (
        'incident_type',
        'status_badge',
        'device_id_short',
        'user',
        'coordinates_link',
        'created_at'
    )
    list_filter = ('incident_type', 'resolved', 'created_at')
    search_fields = ('device_id', 'user__username')
    readonly_fields = ('id', 'created_at')
    actions = ['mark_as_resolved']

    def status_badge(self, obj):
        if obj.resolved:
            return format_html('<span style="color: #2e7d32; font-weight: bold;">✓ Resolved</span>')
        return format_html('<span style="color: #d32f2f; font-weight: bold;">⚠ ACTIVE ALERT</span>')
    status_badge.short_description = "Status"

    def device_id_short(self, obj) -> str:
        return f"{obj.device_id[:12]}..."
    device_id_short.short_description = "Device ID"

    def coordinates_link(self, obj):
        if obj.latitude is not None and obj.longitude is not None:
            url = f"https://maps.google.com/?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank" rel="noopener" style="font-weight: bold; color: #5b3df5;">📍 View Map ({}, {})</a>',
                url, obj.latitude, obj.longitude
            )
        return "No GPS reported"
    coordinates_link.short_description = "GPS Location"

    @admin.action(description="Mark selected incidents as resolved")
    def mark_as_resolved(self, request, queryset):
        count = queryset.update(resolved=True)
        self.message_user(request, f"Marked {count} incident(s) as resolved.")


@admin.register(DailyAnalyticsSummary)
class DailyAnalyticsSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'total_sessions',
        'total_hazards_detected',
        'total_incidents',
        'unique_devices',
        'average_fps'
    )
    list_filter = ('date',)
    ordering = ('-date',)
    readonly_fields = ('created_at',)

    def changelist_view(self, request, extra_context=None):
        """Inject aggregate KPI metrics for top header dashboard cards."""
        extra_context = extra_context or {}
        aggregates = DailyAnalyticsSummary.objects.aggregate(
            all_sessions=Sum('total_sessions'),
            all_hazards=Sum('total_hazards_detected'),
            all_incidents=Sum('total_incidents'),
        )
        extra_context['total_all_sessions'] = aggregates.get('all_sessions') or 0
        extra_context['total_all_hazards'] = aggregates.get('all_hazards') or 0
        extra_context['total_all_incidents'] = aggregates.get('all_incidents') or 0
        extra_context['total_devices'] = UsageEvent.objects.values('device_id').distinct().count()

        return super().changelist_view(request, extra_context=extra_context)
