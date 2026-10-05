"""
URL Configuration for Netra Analytics and Incident endpoints.
"""
from django.urls import path
from .views import RecordEventsView, ReportSafetyIncidentView

urlpatterns = [
    path('events/', RecordEventsView.as_view(), name='record-events'),
    path('incidents/', ReportSafetyIncidentView.as_view(), name='report-incident'),
]
