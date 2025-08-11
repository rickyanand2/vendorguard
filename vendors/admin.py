# vendors/admin.py
from django.contrib import admin
from .models import (
    Vendor,
    VendorOffering,
    VendorContact,
    VendorDomain,
    VendorDocument,
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "status",
        "tier",
        "criticality",
        "risk_rating",
        "last_assessed",
    )
    list_filter = ("organization", "status", "tier", "criticality")
    search_fields = ("name", "website", "description")
    autocomplete_fields = ("organization", "created_by")


@admin.register(VendorOffering)
class VendorOfferingAdmin(admin.ModelAdmin):
    list_display = ("vendor", "name", "service_type", "data_classification")
    list_filter = ("service_type", "data_classification")
    search_fields = ("name", "vendor__name")
    autocomplete_fields = ("vendor",)


@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ("vendor", "name", "email", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("name", "email", "vendor__name")
    autocomplete_fields = ("vendor",)


@admin.register(VendorDomain)
class VendorDomainAdmin(admin.ModelAdmin):
    list_display = ("vendor", "domain")
    search_fields = ("domain", "vendor__name")
    autocomplete_fields = ("vendor",)


@admin.register(VendorDocument)
class VendorDocumentAdmin(admin.ModelAdmin):
    list_display = ("vendor", "doc_type", "title", "issued_date", "expires_date")
    list_filter = ("doc_type",)
    search_fields = ("title", "vendor__name")
    autocomplete_fields = ("vendor",)
