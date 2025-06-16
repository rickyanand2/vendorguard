"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

from django.contrib.auth import views as auth_views

from accounts import views  # ✅ Your custom register view
from accounts.views import home  # ✅ import the homepage view

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView  # For logout functionality
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    # ✅ Profile view URL
    path("accounts/profile/", views.profile, name="profile"),
    # ✅ Auth routes
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    # ✅ Django auth extras (password_reset etc.)
    path("accounts/", include("django.contrib.auth.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
