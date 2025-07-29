# vendors/urls.py

from django.urls import path
from vendors.views import (
    VendorListView,
    VendorDetailView,
    VendorCreateView,
    VendorUpdateView,
    VendorArchiveView,
    VendorOfferingListView,
    VendorOfferingCreateView,
    VendorOfferingUpdateView,
    VendorOfferingDetailView,
    VendorOfferingArchiveView,
)

app_name = "vendors"

urlpatterns = [
    # ──────────────── Vendor Views ────────────────
    path("", VendorListView.as_view(), name="vendor_list"),
    path("new/", VendorCreateView.as_view(), name="vendor_create"),
    path("<int:pk>/", VendorDetailView.as_view(), name="vendor_detail"),
    path("<int:pk>/edit/", VendorUpdateView.as_view(), name="vendor_update"),
    path("<int:pk>/archive/", VendorArchiveView.as_view(), name="vendor_archive"),
    # ───────────── Vendor Offering Views ─────────────
    path("offerings/", VendorOfferingListView.as_view(), name="offering_list"),
    path(
        "offerings/new/<int:vendor_id>/",
        VendorOfferingCreateView.as_view(),
        name="offering_create",
    ),
    path(
        "offerings/<int:pk>/",
        VendorOfferingDetailView.as_view(),
        name="offering_detail",
    ),
    path(
        "offerings/<int:pk>/edit/",
        VendorOfferingUpdateView.as_view(),
        name="offering_update",
    ),
    path(
        "offerings/<int:pk>/archive/",
        VendorOfferingArchiveView.as_view(),
        name="offering_archive",
    ),
]
