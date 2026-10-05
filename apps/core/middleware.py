"""
Core Middlewares for Netra:
- RequestIDMiddleware: Assigns and tracks a unique X-Request-Id per HTTP request.
- DeviceIDMiddleware: Extracts and validates anonymous X-Device-Id from headers.
- SecurityHeadersMiddleware: Sets baseline security and permissions policies.
"""
import uuid
from typing import Callable
from django.http import HttpRequest, HttpResponse


class RequestIDMiddleware:
    """
    Ensures every incoming request has a unique correlation ID for structured tracing.
    If X-Request-Id is passed by a proxy/client, it is preserved; otherwise a new UUID is generated.
    """
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        req_id = request.headers.get("X-Request-Id")
        if not req_id:
            req_id = str(uuid.uuid4())
        
        request.id = req_id
        response = self.get_response(request)
        response["X-Request-Id"] = req_id
        return response


class DeviceIDMiddleware:
    """
    Extracts the X-Device-Id header sent by the client.
    Allows anonymous usage to seamlessly interact with backend settings, devices,
    and telemetry without requiring an authenticated user account.
    """
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        device_id_raw = request.headers.get("X-Device-Id")
        cleaned_device_id = None
        if device_id_raw:
            cleaned_device_id = device_id_raw.strip()
            # If standard UUID format, validate/normalize
            try:
                cleaned_device_id = str(uuid.UUID(cleaned_device_id))
            except (ValueError, AttributeError):
                # Allow standard alphanumeric IDs if non-UUID
                cleaned_device_id = cleaned_device_id[:64]

        request.device_id = cleaned_device_id
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """
    Adds security headers to all responses.
    Camera is permitted for the same origin (required for obstacle vision).
    """
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permit camera for on-device/cloud navigation
        response["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"
        return response
