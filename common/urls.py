# common/urls.py

from django.urls import path

from .views import CommonTestLayoutView

app_name = "common"

urlpatterns = [
    path("test-layout/", CommonTestLayoutView.as_view(), name="test_layout"),
]
