"""
URL routing for Netra Core app.
Provides:
- Core system API endpoints (/api/health/, /api/version/)
- Web frontend pages and PWA routes (/, /navigate/, /demo/, /offline/)
"""
from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/health/', views.HealthCheckView.as_view(), name='api-health'),
    path('api/version/', views.VersionView.as_view(), name='api-version'),

    # Frontend routes (matching exact design system)
    path('', views.HomeView.as_view(), name='home'),
    path('navigate/', views.NavigateView.as_view(), name='navigate'),
    path('demo/', views.DemoView.as_view(), name='demo'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('offline/', views.OfflineView.as_view(), name='offline'),
]
