# website/urls.py
from django.urls import path
from . import views

app_name = "website"  # very important for namespacing

urlpatterns = [
    path("", views.home, name="home"),  # This supports reverse("website:home")
]
