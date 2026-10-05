"""
Django Admin integration for Netra ModelHub.
Includes:
- Checksum integrity display
- Active status toggling
- Custom Action: Hot-reload active PyTorch model into live server InferenceService
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.detection.services.inference import InferenceService
from .models import ModelVersion


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = (
        'version',
        'model_type',
        'is_active_badge',
        'imgsz',
        'sha256_short',
        'uploaded_at'
    )
    list_filter = ('model_type', 'is_active', 'uploaded_at')
    search_fields = ('version', 'release_notes', 'sha256_checksum')
    readonly_fields = ('sha256_checksum', 'uploaded_at')
    actions = ['activate_selected_model', 'hot_reload_into_inference_engine']

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #2e7d32; font-weight: bold;">● Active</span>')
        return format_html('<span style="color: #757575;">Inactive</span>')
    is_active_badge.short_description = "Status"

    def sha256_short(self, obj) -> str:
        if obj.sha256_checksum:
            return f"{obj.sha256_checksum[:12]}..."
        return "-"
    sha256_short.short_description = "SHA-256"

    @admin.action(description="Activate selected model for its format type")
    def activate_selected_model(self, request, queryset):
        for model in queryset:
            model.is_active = True
            model.save()
        self.message_user(request, "Selected model activated. Other versions of the same format were deactivated.")

    @admin.action(description="Hot-reload into live Server Inference Engine")
    def hot_reload_into_inference_engine(self, request, queryset):
        """
        Hot-reloads the selected PyTorch weights directly into the running YOLO
        InferenceService singleton without restarting the Daphne ASGI server.
        """
        model = queryset.first()
        if not model:
            return

        if model.model_type != 'yolo_pt':
            self.message_user(
                request,
                f"Model '{model.version}' is '{model.get_model_type_display()}'. Only PyTorch ('yolo_pt') weights can be hot-reloaded into server memory.",
                level='warning'
            )
            return

        try:
            model.is_active = True
            model.save()

            weights_path = model.weights_file.path
            inference = InferenceService.get_instance()
            inference.reload_model(weights_path)

            self.message_user(
                request,
                f"Success! Model '{model.version}' hot-reloaded into server InferenceService in real time."
            )
        except Exception as e:
            self.message_user(
                request,
                f"Hot-reload failed: {str(e)}",
                level='error'
            )
