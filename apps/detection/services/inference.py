"""
Singleton Computer Vision Inference Service for Netra.
Handles:
- Singleton lifecycle for Ultralytics YOLO models per worker process
- Asynchronous execution in ThreadPoolExecutor to prevent event-loop latency
- Dynamic model hot-reloading on ModelVersion activation
- Monocular distance estimation (real-world object heights) and directional binning
- Graceful fallback when weights are absent or in mocked unit test runs
"""
import io
import time
import logging
import threading
import concurrent.futures
from typing import List, Dict, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)


from .constants import (
    REAL_WORLD_HEIGHTS_M,
    DEFAULT_OBJECT_HEIGHT_M,
    DEFAULT_FOCAL_FACTOR,
    DIRECTION_THRESHOLDS,
)


class InferenceService:
    """
    Singleton service managing Computer Vision inference for Netra.
    Supports:
    - Google Gemini Vision (cloud API, zero model weights, zero PyTorch OOM)
    - Ultralytics YOLOv8 (local PyTorch weights when available)
    - Lightweight heuristic fallback for offline zero-weight operation
    """
    _instance: Optional["InferenceService"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._model = None
        self._model_name: str = "yolov8n"
        self._backend: str = "auto"
        self._loaded: bool = False
        self._load_error: Optional[str] = None
        self._focal_factor: float = DEFAULT_FOCAL_FACTOR
        self._mock_inference_func = None
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="netra_vision"
        )
        self.load_model()

    @classmethod
    def get_instance(cls) -> "InferenceService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def is_loaded(self) -> bool:
        return self._loaded or (self._mock_inference_func is not None)

    def set_mock_model(self, mock_func) -> None:
        """
        Enables mocking predictions for instant, zero-weight unit test execution.
        """
        self._mock_inference_func = mock_func
        self._loaded = True

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Loads the active vision model or initializes Gemini Vision backend.
        """
        from django.conf import settings
        backend_pref = getattr(settings, "VISION_BACKEND", "auto").lower()

        # If explicitly set to Gemini
        if backend_pref == "gemini":
            self._backend = "gemini"
            self._model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
            self._loaded = True
            self._load_error = None
            return True

        # Attempt to load YOLO if available and requested
        try:
            # 1. Check active ModelVersion from modelhub
            if not model_path:
                try:
                    from apps.modelhub.models import ModelVersion
                    active_version = ModelVersion.objects.filter(model_type='yolo_pt', is_active=True).first()
                    if active_version and active_version.weights_file:
                        model_path = active_version.weights_file.path
                        self._model_name = active_version.version
                except Exception:
                    pass

            if not model_path:
                model_path = "yolov8n.pt"

            from ultralytics import YOLO
            self._model = YOLO(model_path)
            self._backend = "yolo"
            self._loaded = True
            self._load_error = None
            return True
        except Exception as e:
            # On cloud deployments (Render, Railway) where YOLO weights or PyTorch fail:
            # Seamlessly switch to Gemini Vision backend
            self._model = None
            self._backend = "gemini"
            self._model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
            self._loaded = True
            self._load_error = None
            logger.info(f"YOLO unavailable ({e}). Activated Gemini Vision backend ({self._model_name}).")
            return True


    def reload_model(self, model_path: Optional[str] = None) -> bool:
        """Hot-reloads model weights into memory."""
        return self.load_model(model_path)

    def hot_reload(self, new_model_path: Optional[str] = None) -> bool:
        """
        Hot-reloads weights dynamically when an administrator activates a new model.
        """
        with self._lock:
            return self.load_model(new_model_path)

    def estimate_distance(self, class_name: str, box_h: float) -> float:
        """
        Estimates real-world distance (in meters) based on normalized box height.
        Distance = (Known Object Height * Focal Factor) / Normalized Box Height
        """
        real_h = REAL_WORLD_HEIGHTS_M.get(class_name.lower(), DEFAULT_OBJECT_HEIGHT_M)
        effective_h = max(0.01, min(1.0, box_h))
        dist = (real_h * self._focal_factor) / effective_h
        # Clamp distance to realistic sensor bounds (0.3m to 25m)
        return round(max(0.3, min(25.0, dist)), 2)

    def classify_direction(self, box_x: float, box_w: float) -> str:
        """
        Categorizes lateral direction ('left', 'ahead', 'right') based on box horizontal center.
        """
        center_x = box_x + (box_w / 2.0)
        if center_x < DIRECTION_THRESHOLDS["left_limit"]:
            return "left"
        elif center_x > DIRECTION_THRESHOLDS["right_limit"]:
            return "right"
        return "ahead"

    def _sync_predict(self, image: Image.Image, imgsz: int = 416, conf: float = 0.35) -> List[Dict[str, Any]]:
        """
        Synchronous prediction pipeline executed inside the worker thread pool.
        """
        # If running in test mode with mocked detector
        if self._mock_inference_func is not None:
            return self._mock_inference_func(image)

        # Route to Gemini Vision backend
        if self._backend == "gemini" or self._model is None:
            from .gemini_service import GeminiService
            return GeminiService.get_instance().detect_obstacles(image)


        # Convert PIL Image to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        orig_w, orig_h = image.size
        if orig_w <= 0 or orig_h <= 0:
            return []

        # Run Ultralytics inference
        results = self._model.predict(
            source=image,
            imgsz=imgsz,
            conf=conf,
            verbose=False,
            device="cpu"  # CPU default; supports auto-device
        )

        detections: List[Dict[str, Any]] = []

        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes
        names = first_res.names

        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            class_name = names.get(cls_id, "object")
            confidence = float(box.conf[0].item())

            # Bounding box xyxy format
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = xyxy

            # Normalize to 0-1
            nx1 = max(0.0, min(1.0, x1 / orig_w))
            ny1 = max(0.0, min(1.0, y1 / orig_h))
            nw = max(0.0, min(1.0, (x2 - x1) / orig_w))
            nh = max(0.0, min(1.0, (y2 - y1) / orig_h))

            box_norm = [round(nx1, 4), round(ny1, 4), round(nw, 4), round(nh, 4)]
            direction = self.classify_direction(nx1, nw)
            distance_m = self.estimate_distance(class_name, nh)

            detections.append({
                "class_name": class_name,
                "confidence": round(confidence, 2),
                "box": box_norm,
                "direction": direction,
                "distance_m": distance_m,
                "approaching": False,
            })

        return detections

    def predict_image(
        self,
        image: Image.Image,
        imgsz: int = 416,
        conf: float = 0.35
    ) -> concurrent.futures.Future:
        """
        Dispatches inference to the thread pool and returns a Future.
        """
        return self._executor.submit(self._sync_predict, image, imgsz, conf)

    def decode_and_predict(
        self,
        image_bytes: bytes,
        imgsz: int = 416,
        conf: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Decodes in-memory image bytes (JPEG) and executes inference synchronously within thread.
        Never writes bytes to disk.
        """
        image = Image.open(io.BytesIO(image_bytes))
        return self._sync_predict(image, imgsz=imgsz, conf=conf)
