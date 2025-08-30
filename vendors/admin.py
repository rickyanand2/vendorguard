# vendors/admin.py — safe admin until the Vendor model is finalized

from django.contrib import admin
from .models import Vendor, VendorOffering, VendorContact, VendorDocument, VendorDomain


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "organization")  # ← removed 'status'
    search_fields = ("name", "organization__name", "website")
    list_filter = ("organization",)  # ← removed 'status'
    autocomplete_fields = ("organization",)
    ordering = ("organization__name", "name")


@admin.register(VendorOffering)
class VendorOfferingAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor")
    search_fields = ("name", "vendor__name")
    list_filter = ("vendor",)
    autocomplete_fields = ("vendor",)
    ordering = ("vendor__name", "name")


@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ("email", "vendor")
    search_fields = ("email", "vendor__name")
    list_filter = ("vendor",)
    autocomplete_fields = ("vendor",)


@admin.register(VendorDocument)
class VendorDocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "vendor")
    search_fields = ("vendor__name",)
    list_filter = ("vendor", "doc_type")
    autocomplete_fields = ("vendor",)


@admin.register(VendorDomain)
class VendorDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "vendor")
    search_fields = ("domain", "vendor__name")
    list_filter = ("vendor",)
    autocomplete_fields = ("vendor",)
