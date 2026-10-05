"""
URL Configuration for Netra ModelHub endpoints.
"""
from django.urls import path
from .views import LatestModelView, ModelDownloadView

urlpatterns = [
    path('models/latest/', LatestModelView.as_view(), name='models-latest'),
    path('models/<str:version>/download/', ModelDownloadView.as_view(), name='models-download'),
]
