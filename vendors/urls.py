# vendors/urls.py

from django.urls import path
from vendors import views
from vendors.views import VendorViews, VendorOfferingViews

app_name = "vendors"

urlpatterns = [
    path("", VendorViews.list, name="vendor_list"),
    path("add/", VendorViews.create, name="vendor_add"),
    path("<int:pk>/", VendorViews.detail, name="vendor_detail"),
    path("<int:pk>/edit/", VendorViews.update, name="vendor_edit"),
    path("<int:pk>/archive/", VendorViews.archive, name="vendor_archive"),
    path("offerings/", VendorOfferingViews.list, name="offering_list"),
    path(
        "vendors/<int:vendor_id>/offerings/add/",
        VendorOfferingViews.create,
        name="offering_add",
    ),
    path("offerings/<int:pk>/edit/", VendorOfferingViews.update, name="offering_edit"),
    path("offerings/<int:pk>/", VendorOfferingViews.detail, name="offering_detail"),
    path(
        "offerings/<int:pk>/archive/",
        VendorOfferingViews.archive,
        name="offering_archive",
    ),
]
