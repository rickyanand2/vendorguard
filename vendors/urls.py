# vendors/urls.py

from django.urls import path

from . import views

app_name = "vendors"

urlpatterns = [
    # ──────────────── Vendor Views ────────────────
    path("", views.vendor_list, name="vendor_list"),
    path("new/", views.vendor_create, name="vendor_create"),
    path("<int:pk>/", views.vendor_detail, name="vendor_detail"),
    path("<int:pk>/edit/", views.vendor_update, name="vendor_update"),
    path("<int:pk>/archive/", views.vendor_archive, name="vendor_archive"),
    # ───────────── Vendor Offering Views ─────────────
    path("offerings/", views.offering_list, name="offering_list"),
    path(
        "offerings/new/<int:vendor_id>/",
        views.offering_create,
        name="offering_create",
    ),
    path(
        "offerings/<int:pk>/",
        views.offering_detail,
        name="offering_detail",
    ),
    path(
        "offerings/<int:pk>/edit/",
        views.offering_update,
        name="offering_update",
    ),
    path(
        "offerings/<int:pk>/archive/",
        views.offering_archive,
        name="offering_archive",
    ),
]
