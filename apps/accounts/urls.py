"""
URL Routing for Netra Accounts API.
Endpoints:
- POST /api/auth/register/
- POST /api/auth/login/
- POST /api/auth/logout/
- POST /api/auth/token/refresh/
- POST /api/devices/
- GET, PUT, PATCH /api/settings/
- CRUD /api/contacts/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'contacts', views.EmergencyContactViewSet, basename='emergency-contacts')

urlpatterns = [
    # Authentication (JWT & Session)
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),

    # Anonymous Device Management
    path('devices/', views.DeviceRegisterView.as_view(), name='devices-register'),

    # Assistive Settings (User or Anonymous Device)
    path('settings/', views.UserSettingsView.as_view(), name='user-settings'),

    # Emergency Contacts Router (max 5 contacts)
    path('', include(router.urls)),
]
