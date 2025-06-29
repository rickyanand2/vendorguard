# vendors/urls.py

from django.urls import path
from vendors import views

app_name = "vendors"

urlpatterns = [
    path("", views.VendorListView.as_view(), name="vendor_list"),
    path("add/", views.VendorCreateView.as_view(), name="vendor_add"),
    path("vendors/<int:pk>/", VendorDetailView.as_view(), name="vendor_detail"),
    path("offerings/", VendorOfferingListView.as_view(), name="offering_list"),
    path("<int:pk>/edit/", views.VendorUpdateView.as_view(), name="vendor_edit"),
    path(
        "<int:pk>/archive/",
        views.VendorArchiveView.as_view(),
        name="vendor_archive",
    ),
]
