"""
REST API Endpoints for Netra Computer Vision Detection, Scene Narration, and OCR.
"""
import time
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from PIL import Image

from apps.core.utils import api_response
from .serializers import (
    ImageUploadSerializer,
    DetectResponseSerializer,
    DescribeResponseSerializer,
    OCRResponseSerializer,
)
from .services.inference import InferenceService
from .services.priority import select_top_hazards
from .services.describe import describe_scene
from .services.ocr import run_ocr


class DetectAPIView(APIView):
    """
    Executes one-shot YOLO computer vision detection on an uploaded image.
    Returns normalized bounding boxes, distance estimates (meters), lateral directions,
    and prioritized top hazards.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="One-Shot Obstacle Detection",
        description="Upload an image (max 2 MB) for monocular obstacle detection, distance estimation, and direction classification.",
        request=ImageUploadSerializer,
        responses={
            200: DetectResponseSerializer,
            400: OpenApiResponse(description="Invalid or oversized image"),
            503: OpenApiResponse(description="Model runtime unavailable (fallback to on-device)"),
        },
        tags=["Detection"]
    )
    def post(self, request) -> Response:
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data["image"]
        imgsz = serializer.validated_data.get("imgsz", 416)

        try:
            pil_img = Image.open(image_file)
        except Exception:
            return api_response(
                message="Unable to decode uploaded image.",
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        start_t = time.perf_counter()
        inference = InferenceService.get_instance()

        try:
            future = inference.predict_image(pil_img, imgsz=imgsz)
            detections = future.result(timeout=5.0)
        except Exception as e:
            return api_response(
                message=f"Cloud detection unavailable: {str(e)}. Use on-device mode.",
                success=False,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        top_hazards = select_top_hazards(detections, limit=2)
        latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

        payload = {
            "items": detections,
            "top": top_hazards,
            "count": len(detections),
            "latency_ms": latency_ms,
        }

        return api_response(data=payload, message="Detections computed successfully.")


class DescribeSceneAPIView(APIView):
    """
    Analyzes an uploaded image, identifies foreground obstacles, and generates
    a warm, natural-language audio narration in English or Hindi.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Generate Natural Language Scene Narration",
        description="Upload an image (max 2 MB) and receive an assistive spoken phrase in English or Hindi.",
        request=ImageUploadSerializer,
        responses={
            200: DescribeResponseSerializer,
            400: OpenApiResponse(description="Invalid or oversized image"),
            503: OpenApiResponse(description="Vision model unavailable"),
        },
        tags=["Detection"]
    )
    def post(self, request) -> Response:
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data["image"]
        language = serializer.validated_data.get("language", "en")
        imgsz = serializer.validated_data.get("imgsz", 416)

        try:
            pil_img = Image.open(image_file)
        except Exception:
            return api_response(
                message="Unable to decode uploaded image.",
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        start_t = time.perf_counter()
        inference = InferenceService.get_instance()

        try:
            future = inference.predict_image(pil_img, imgsz=imgsz)
            detections = future.result(timeout=5.0)
        except Exception as e:
            return api_response(
                message=f"Cloud scene description unavailable: {str(e)}",
                success=False,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        description = describe_scene(detections, language=language)
        latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

        payload = {
            "text": description["text"],
            "items": description["items"],
            "language": description["language"],
            "latency_ms": latency_ms,
        }

        return api_response(data=payload, message="Scene description generated.")


class OCRAPIView(APIView):
    """
    Extracts text from street signage, building markers, and public bus boards
    in English and Hindi (Devanagari).
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Extract Text from Street Signage (OCR)",
        description="Reads text blocks from an image with bounding boxes and lateral directions.",
        request=ImageUploadSerializer,
        responses={200: OCRResponseSerializer},
        tags=["Detection"]
    )
    def post(self, request) -> Response:
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data["image"]
        language = serializer.validated_data.get("language", "en")

        try:
            pil_img = Image.open(image_file)
        except Exception:
            return api_response(
                message="Unable to decode uploaded image.",
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        start_t = time.perf_counter()
        future = run_ocr(pil_img, language=language)

        try:
            blocks = future.result(timeout=6.0)
        except Exception:
            blocks = []

        combined_text = " ".join([b["text"] for b in blocks])
        latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

        payload = {
            "blocks": blocks,
            "count": len(blocks),
            "combined_text": combined_text,
            "latency_ms": latency_ms,
        }

        return api_response(data=payload, message="OCR processing completed.")
