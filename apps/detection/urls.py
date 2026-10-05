"""
URL Routing for Netra Detection & Vision API.
Endpoints:
- POST /api/detect/
- POST /api/describe/
- POST /api/ocr/
"""
from django.urls import path
from . import views

urlpatterns = [
    path('detect/', views.DetectAPIView.as_view(), name='detect'),
    path('describe/', views.DescribeSceneAPIView.as_view(), name='describe'),
    path('ocr/', views.OCRAPIView.as_view(), name='ocr'),
]
