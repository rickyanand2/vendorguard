# Path: thirdparties/urls.py
"""
URL routes for Third Parties and their Services.
We expose both "service" and "solution" routes; they map to the same views.
"""

from django.urls import path
from . import views

app_name = "thirdparties"

urlpatterns = [
    # ─────────────────────────────────────────
    # Third Parties
    # ─────────────────────────────────────────
    path("", views.thirdparty_list, name="thirdparty_list"),
    path("new/", views.thirdparty_create, name="thirdparty_create"),
    path("<int:pk>/", views.thirdparty_detail, name="thirdparty_detail"),
    path("<int:pk>/edit/", views.thirdparty_update, name="thirdparty_update"),
    path("<int:pk>/archive/", views.thirdparty_archive, name="thirdparty_archive"),
    # ─────────────────────────────────────────
    # Services (canonical code-level endpoints)
    # ─────────────────────────────────────────
    path("services/", views.service_list, name="service_list"),
    path(
        "<int:thirdparty_id>/services/new/", views.service_create, name="service_create"
    ),
    path("services/<int:pk>/", views.service_detail, name="service_detail"),
    path("services/<int:pk>/edit/", views.service_update, name="service_update"),
    path("services/<int:pk>/archive/", views.service_archive, name="service_archive"),
    # ─────────────────────────────────────────
    # Solutions (UI-friendly aliases to same views)
    # ─────────────────────────────────────────
    path("solutions/", views.service_list, name="solution_list"),
    path(
        "<int:thirdparty_id>/solutions/new/",
        views.service_create,
        name="solution_create",
    ),
    path("solutions/<int:pk>/", views.service_detail, name="solution_detail"),
    path("solutions/<int:pk>/edit/", views.service_update, name="solution_update"),
    path("solutions/<int:pk>/archive/", views.service_archive, name="solution_archive"),
]
