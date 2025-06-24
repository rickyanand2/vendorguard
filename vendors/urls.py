# vendors/urls.py

from django.urls import path
from . import views

app_name = "vendors"

urlpatterns = [
    path("", views.vendor_list, name="vendor_list"),
    path("add/", views.vendor_add, name="vendor_add"),
    path("<int:vendor_id>/edit/", views.vendor_edit, name="vendor_edit"),
    path("<int:vendor_id>/archive/", views.vendor_archive, name="vendor_archive"),
    path("solutions/add/<int:vendor_id>/", views.add_solution, name="add_solution"),
]
