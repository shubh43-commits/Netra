"""
Core utilities and standard DRF response handlers for Netra.
"""
from typing import Any, Optional, Dict
from rest_framework.views import exception_handler
from rest_framework.response import Response


def api_response(
    data: Optional[Any] = None,
    message: str = "Success",
    success: bool = True,
    status_code: int = 200,
    errors: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Response:
    """
    Standardizes JSON API responses across all Netra endpoints.
    """
    payload = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
    }
    if errors:
        payload["errors"] = errors
    if meta:
        payload["meta"] = meta

    return Response(payload, status=status_code)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    Custom DRF exception handler ensuring consistent error structure:
    {
        "success": false,
        "message": str,
        "errors": dict|list|str,
        "request_id": str (if present)
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        request = context.get("request")
        request_id = getattr(request, "id", None) if request else None

        detail_message = "An error occurred."
        if isinstance(response.data, dict):
            if "detail" in response.data:
                detail_message = str(response.data["detail"])
            elif "message" in response.data:
                detail_message = str(response.data["message"])

        formatted_data = {
            "success": False,
            "message": detail_message,
            "errors": response.data,
        }
        if request_id:
            formatted_data["request_id"] = request_id

        response.data = formatted_data

    return response
