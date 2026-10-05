"""
Models for Netra ModelHub.
Manages:
- Versioned ONNX, PyTorch, and TFLite model weights
- Automated SHA-256 integrity calculation
- Active model selection per model type
- Compatibility verification with client app versions
"""
import hashlib
from django.db import models


def model_weights_path(instance, filename: str) -> str:
    """Store weights partitioned by version and filename."""
    return f"models/{instance.version}/{filename}"


class ModelVersion(models.Model):
    MODEL_TYPE_CHOICES = [
        ('onnx_web', 'ONNX Web (Client In-Browser)'),
        ('yolo_pt', 'PyTorch YOLO (Server Inference)'),
        ('tflite', 'TFLite (Mobile Optimized)'),
        ('tensorrt', 'TensorRT (Edge Acceleration)'),
    ]

    version = models.CharField(max_length=32, unique=True, help_text="Semantic version string, e.g. 'v1.0.0'")
    model_type = models.CharField(max_length=32, choices=MODEL_TYPE_CHOICES, default='onnx_web')
    weights_file = models.FileField(upload_to=model_weights_path)
    sha256_checksum = models.CharField(max_length=64, blank=True, db_index=True)
    min_app_version = models.CharField(max_length=32, default="1.0.0")
    imgsz = models.IntegerField(default=416, help_text="Inference image resolution (e.g. 320, 416, 640)")
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="If checked, this version is served as the active production model for its type."
    )
    release_notes = models.TextField(blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Model Version'
        verbose_name_plural = 'Model Versions'

    def __str__(self) -> str:
        status = " [ACTIVE]" if self.is_active else ""
        return f"{self.version} ({self.get_model_type_display()}){status}"

    def calculate_sha256(self) -> str:
        """Computes SHA-256 hash of the uploaded weights file in chunks."""
        hasher = hashlib.sha256()
        try:
            self.weights_file.seek(0)
            for chunk in self.weights_file.chunks(chunk_size=65536):
                hasher.update(chunk)
            self.weights_file.seek(0)
            return hasher.hexdigest()
        except Exception:
            return ""

    def save(self, *args, **kwargs):
        # Auto-calculate SHA-256 if not provided
        if not self.sha256_checksum and self.weights_file:
            self.sha256_checksum = self.calculate_sha256()

        # If activating this version, deactivate all other models of the same type
        if self.is_active:
            ModelVersion.objects.filter(model_type=self.model_type, is_active=True).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)
