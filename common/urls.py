# common/urls.py

from django.urls import path
from .views import CommonTestLayoutView

urlpatterns = [
    path("test-layout/", CommonTestLayoutView.as_view(), name="test_layout"),
]
