# common/admin.py
from django.contrib import admin

from .models import DataType


@admin.register(DataType)
class DataTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "risk_score", "is_active")
    search_fields = ("code", "label")
