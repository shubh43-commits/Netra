"""
Admin interface registration for Netra Accounts.
"""
from django.contrib import admin
from .models import Device, UserSettings, EmergencyContact


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "platform", "app_version", "analytics_opt_in", "last_seen", "created_at"]
    list_filter = ["platform", "analytics_opt_in", "created_at"]
    search_fields = ["id", "user__username", "user__email"]
    readonly_fields = ["id", "created_at", "last_seen"]


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ["id", "target_owner", "language", "model_size", "detection_mode", "fall_detection_enabled", "updated_at"]
    list_filter = ["language", "model_size", "detection_mode", "vibration", "spatial_beeps", "fall_detection_enabled"]
    search_fields = ["user__username", "device__id"]

    def target_owner(self, obj):
        return obj.user.username if obj.user else f"Device: {obj.device_id}"
    target_owner.short_description = "Owner"


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "phone", "relationship", "target_owner", "created_at"]
    list_filter = ["relationship", "created_at"]
    search_fields = ["name", "phone", "user__username", "device__id"]

    def target_owner(self, obj):
        return obj.user.username if obj.user else f"Device: {obj.device_id}"
    target_owner.short_description = "Belongs To"
