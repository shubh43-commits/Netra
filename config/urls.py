"""
Root URL configuration for Netra AI.

Routes:
- Admin interface: /admin/
- Language switcher: /i18n/
- OpenAPI schema & interactive docs:
  - /api/schema/
  - /api/docs/ (Swagger UI)
  - /api/redoc/ (ReDoc)
- Service Worker & PWA root endpoints: /sw.js, /manifest.webmanifest
- Core app (Health, Version, Web UI): /
- Accounts API: /api/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from apps.core.views import ServiceWorkerView, ManifestView
from apps.accounts.views import UserLoginView, UserSignupView, UserLogoutView, UserProfileView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Web Authentication & Profile Routes (Phone-Responsive)
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('signup/', UserSignupView.as_view(), name='user-signup'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Built-in i18n language switch endpoint (/i18n/setlang/)
    path('i18n/', include('django.conf.urls.i18n')),

    # Root PWA handlers
    path('sw.js', ServiceWorkerView.as_view(), name='service_worker_root'),
    path('manifest.webmanifest', ManifestView.as_view(), name='manifest_root'),

    # OpenAPI Schema & API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Application APIs & Routes
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.detection.urls')),
    path('api/', include('apps.feedback.urls')),
    path('api/', include('apps.modelhub.urls')),
    path('api/', include('apps.analytics.urls')),
    path('', include('apps.core.urls')),
]

# Development static and media serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
