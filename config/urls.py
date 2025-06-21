# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "", include("website.urls", namespace="website")
    ),  # 👈 Homepage and public pages
    path("accounts/", include("accounts.urls")),  # Register, login, profile, etc.
    # Built-in auth views: password reset, etc.
    path("accounts/", include("django.contrib.auth.urls")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
]

# Serve static files in dev mode
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
