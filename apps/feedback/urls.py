"""
URL Configuration for Netra Feedback app.
"""
from django.urls import path
from .views import ReportFeedbackView

urlpatterns = [
    path('feedback/report/', ReportFeedbackView.as_view(), name='feedback-report'),
]
