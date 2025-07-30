# dashboard/urls.py
from django.urls import path

from .views import DashboardStatsView, UserDashboardView

app_name = "dashboard"

urlpatterns = [
    path("", UserDashboardView.as_view(), name="dashboard"),
    path("data/", DashboardStatsView.as_view(), name="dashboard_data"),
]
