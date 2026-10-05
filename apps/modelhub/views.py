"""
API Views for Netra ModelHub.
Provides:
- GET /api/models/latest/ : Returns active model metadata, checksum, and download URL
- GET /api/models/<version>/download/ : Downloads weights file
"""
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.core.utils import api_response
from .models import ModelVersion
from .serializers import ModelVersionSerializer


class LatestModelView(APIView):
    """
    Returns the latest production AI model metadata, including download URL,
    SHA-256 integrity hash, and recommended input dimensions.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Get Latest Active AI Model",
        description="Returns latest active AI model weights for in-browser client inference (ONNX) or server inference (PyTorch).",
        parameters=[
            OpenApiParameter(
                name="model_type",
                type=str,
                default="onnx_web",
                description="Target model format: onnx_web, yolo_pt, tflite, tensorrt"
            )
        ],
        responses={
            200: ModelVersionSerializer,
            404: OpenApiResponse(description="No model version found for requested type"),
        },
        tags=["ModelHub"]
    )
    def get(self, request, *args, **kwargs) -> Response:
        model_type = request.query_params.get('model_type', 'onnx_web')

        # 1. Search for active model first
        model = ModelVersion.objects.filter(model_type=model_type, is_active=True).first()

        # 2. Fall back to most recent uploaded model if none explicitly marked active
        if not model:
            model = ModelVersion.objects.filter(model_type=model_type).first()

        if not model:
            return api_response(
                success=False,
                message=f"No model version registered for type '{model_type}'.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = ModelVersionSerializer(model, context={'request': request})
        return api_response(
            success=True,
            message="Latest model metadata retrieved.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class ModelDownloadView(APIView):
    """
    Downloads raw model weights file with appropriate content headers.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Download Model Weights File",
        description="Downloads the binary model weights (e.g., .onnx, .pt, .tflite).",
        responses={200: OpenApiResponse(description="Binary weights file download")},
        tags=["ModelHub"]
    )
    def get(self, request, version: str, *args, **kwargs):
        model = get_object_or_404(ModelVersion, version=version)
        if not model.weights_file:
            raise Http404("Weights file does not exist.")

        return FileResponse(
            model.weights_file.open('rb'),
            as_attachment=True,
            filename=model.weights_file.name.split('/')[-1]
        )
