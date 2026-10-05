"""
Django Admin integration for Netra Feedback Reports.
Includes:
- Thumbnail image previews
- Review state management
- Bulk Action: Export selected reports as a ready-to-train YOLO dataset ZIP
"""
import io
import zipfile
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import DetectionReport


@admin.register(DetectionReport)
class DetectionReportAdmin(admin.ModelAdmin):
    list_display = (
        'short_id',
        'thumbnail_preview',
        'issue_type',
        'device_id',
        'user',
        'is_reviewed',
        'created_at'
    )
    list_filter = ('issue_type', 'is_reviewed', 'created_at')
    search_fields = ('id', 'device_id', 'user_note', 'user__username')
    readonly_fields = ('id', 'image_preview', 'created_at')
    actions = ['mark_as_reviewed', 'export_as_yolo_dataset']

    def short_id(self, obj) -> str:
        return str(obj.id)[:8]
    short_id.short_description = "ID"

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid #15121f;" />',
                obj.image.url
            )
        return "-"
    thumbnail_preview.short_description = "Frame"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 480px; max-height: 480px; border-radius: 12px; border: 2px solid #15121f;" />',
                obj.image.url
            )
        return "No image uploaded."
    image_preview.short_description = "High-Res Image"

    @admin.action(description="Mark selected reports as reviewed")
    def mark_as_reviewed(self, request, queryset):
        count = queryset.update(is_reviewed=True)
        self.message_user(request, f"Successfully marked {count} reports as reviewed.")

    @admin.action(description="Export selected reports as YOLO dataset ZIP")
    def export_as_yolo_dataset(self, request, queryset):
        """
        Bundles selected report images and label annotations into a standard
        Ultralytics YOLO dataset zip archive (images/, labels/, data.yaml).
        """
        zip_buffer = io.BytesIO()

        # Standard assistive hazard class mapping
        classes = ['person', 'car', 'stairs', 'pothole', 'pole', 'door', 'auto_rickshaw', 'hazard']
        class_to_idx = {c: i for i, c in enumerate(classes)}

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Write data.yaml specification
            yaml_content = (
                "path: ./\n"
                "train: images/\n"
                "val: images/\n"
                "names:\n" +
                "\n".join([f"  {idx}: {name}" for idx, name in enumerate(classes)]) +
                "\n"
            )
            zf.writestr('data.yaml', yaml_content)

            # 2. Process each report
            for report in queryset:
                if not report.image:
                    continue

                clean_id = str(report.id)[:12]
                img_name = f"images/{clean_id}.jpg"
                lbl_name = f"labels/{clean_id}.txt"

                # Read and add image content
                try:
                    report.image.seek(0)
                    img_bytes = report.image.read()
                    zf.writestr(img_name, img_bytes)
                except Exception:
                    continue

                # Generate YOLO label lines: <class_idx> <x_center> <y_center> <width> <height>
                label_lines = []
                boxes = report.metadata.get('boxes', [])

                if isinstance(boxes, list) and len(boxes) > 0:
                    for b in boxes:
                        if isinstance(b, dict):
                            c_name = b.get('class_name', 'hazard')
                            c_idx = class_to_idx.get(c_name, class_to_idx['hazard'])
                            coords = b.get('box', [0.5, 0.5, 0.2, 0.2])
                            if len(coords) == 4:
                                label_lines.append(f"{c_idx} {coords[0]} {coords[1]} {coords[2]} {coords[3]}")
                else:
                    # Default center box if issue was missed obstacle
                    c_idx = class_to_idx.get(report.issue_type, class_to_idx['hazard'])
                    label_lines.append(f"{c_idx} 0.5 0.5 0.3 0.3")

                zf.writestr(lbl_name, "\n".join(label_lines) + "\n")

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="netra_yolo_feedback_dataset.zip"'
        return response
