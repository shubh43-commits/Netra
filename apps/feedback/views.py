"""
API Views for User Detection Feedback and Reporting.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.utils import api_response
from .serializers import DetectionReportSerializer


class ReportFeedbackView(APIView):
    """
    Submits a misclassification report with camera image and optional annotations.
    Accepts reports from both authenticated accounts and anonymous devices.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Submit Detection Bug Report",
        description="Allows visually impaired users or test testers to submit false alarms or missed obstacles with camera frames for model retraining.",
        request=DetectionReportSerializer,
        responses={
            201: OpenApiResponse(description="Report submitted successfully"),
            400: OpenApiResponse(description="Validation or file size error"),
        },
        tags=["Feedback"]
    )
    def post(self, request, *args, **kwargs) -> Response:
        serializer = DetectionReportSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_response(
                success=False,
                message="Invalid report submission.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        report = serializer.save()
        return api_response(
            success=True,
            message="Detection report submitted successfully. Thank you for improving Netra.",
            data={
                "report_id": str(report.id),
                "issue_type": report.issue_type,
                "created_at": report.created_at.isoformat(),
            },
            status_code=status.HTTP_201_CREATED
        )
