"""
Core views and API endpoints for Netra AI.
Provides:
- HealthCheckView: Verifies database, cache/redis, and model runtime health.
- VersionView: Returns system and API version metadata.
- PWA and Frontend views: HomeView, NavigateView, DemoView, OfflineView, ServiceWorkerView, ManifestView.
"""
import os
import time
from typing import Dict, Any

from django.conf import settings
from django.db import connection
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView, View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .utils import api_response
from .serializers import HealthCheckResponseSerializer, VersionResponseSerializer


class HealthCheckView(APIView):
    """
    Evaluates backend services and returns real-time health telemetry.
    Checks:
    - Primary relational database
    - Redis cache and message broker connectivity
    - YOLO AI model loaded status
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="System Health Telemetry",
        description="Checks database, Redis broker, and computer vision model status.",
        responses={
            200: HealthCheckResponseSerializer,
            503: HealthCheckResponseSerializer,
        },
        tags=["Core"]
    )
    def get(self, request, *args, **kwargs) -> Response:
        checks: Dict[str, Any] = {
            "database": "unknown",
            "redis": "unknown",
            "model_loaded": False,
        }
        all_ok = True

        # 1. Database check
        try:
            connection.ensure_connection()
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"
            all_ok = False

        # 2. Redis check
        redis_url = getattr(settings, "REDIS_URL", "")
        if redis_url:
            try:
                import redis
                r = redis.from_url(redis_url, socket_connect_timeout=1.0)
                r.ping()
                checks["redis"] = "ok"
            except Exception as e:
                checks["redis"] = f"unavailable: {str(e)}"
                # Redis down in development is tolerable (in-memory fallback)
                if not settings.DEBUG:
                    all_ok = False
        else:
            checks["redis"] = "in-memory (dev mode)"

        # 3. Model Loaded Check
        try:
            # Check inference singleton if available
            from apps.detection.services.inference import InferenceService
            checks["model_loaded"] = InferenceService.get_instance().is_loaded()
        except (ImportError, Exception):
            checks["model_loaded"] = False

        status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        payload = {
            "status": "healthy" if all_ok else "degraded",
            "services": checks,
            "environment": "development" if settings.DEBUG else "production",
            "timestamp": int(time.time()),
            "version": getattr(settings, "APP_VERSION", "1.0.0"),
        }

        return Response(payload, status=status_code)


class VersionView(APIView):
    """
    Exposes app information, API version, and supported locale languages.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Application & API Version Info",
        description="Returns release version, API version, and supported assistive languages.",
        responses={200: VersionResponseSerializer},
        tags=["Core"]
    )
    def get(self, request, *args, **kwargs) -> Response:
        return Response({
            "app": "Netra",
            "tagline": "Your phone just got eyes",
            "version": getattr(settings, "APP_VERSION", "1.0.0"),
            "api_version": "v1",
            "supported_languages": [code for code, _ in settings.LANGUAGES],
            "docs_url": "/api/docs/",
            "offline_url": "/offline/",
        })


# ==============================================================================
# Frontend Template & PWA Views (matching exact design system)
# ==============================================================================

class HomeView(TemplateView):
    template_name = 'home.html'


class NavigateView(TemplateView):
    template_name = 'navigate.html'


class DemoView(TemplateView):
    template_name = 'demo.html'


class OfflineView(TemplateView):
    template_name = 'offline.html'


class SettingsView(TemplateView):
    template_name = 'settings.html'


class ServiceWorkerView(View):
    def get(self, request, *args, **kwargs):
        sw_path = settings.BASE_DIR / 'static' / 'sw.js'
        if not os.path.exists(sw_path):
            raise Http404("Service Worker script not found.")

        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()

        response = HttpResponse(content, content_type='application/javascript; charset=utf-8')
        response['Service-Worker-Allowed'] = '/'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response


class ManifestView(View):
    def get(self, request, *args, **kwargs):
        manifest_path = settings.BASE_DIR / 'static' / 'manifest.webmanifest'
        if not os.path.exists(manifest_path):
            raise Http404("Manifest file not found.")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        response = HttpResponse(content, content_type='application/manifest+json; charset=utf-8')
        response['Cache-Control'] = 'public, max-age=86400'
        return response
