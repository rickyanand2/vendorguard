from django.contrib import admin
from .models import Vendor, VendorTrustProfile, Certification, Solution


class CertificationInline(admin.StackedInline):
    model = Certification
    extra = 1
    fields = (
        "type",
        "issued_date",
        "expiry_date",
        "cert_number",
        "artifact",
        "external_url",
        "notes",
    )
    readonly_fields = ()
    show_change_link = True
    classes = ["collapse"]


@admin.register(VendorTrustProfile)
class VendorTrustProfileAdmin(admin.ModelAdmin):
    list_display = [
        "vendor",
        "has_cyber_insurance",
        "has_data_breach",
        "last_breach_date",
        "trust_score",
        "certifications_summary",
    ]

    def certifications_summary(self, obj):
        if obj.vendor_id:
            certs = obj.vendor.certifications.all()
            return ", ".join([cert.get_type_display() for cert in certs]) or "None"
        return "N/A"

    certifications_summary.short_description = "Certifications"
    readonly_fields = ["trust_score"]
    actions = ["recalculate_scores"]

    @admin.action(description="Recalculate trust scores")
    def recalculate_scores(self, request, queryset):
        for profile in queryset:
            profile.calculate_trust_score()
            profile.save()


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "industry", "contact_email", "created_at"]
    search_fields = ("name", "organization", "industry", "contact_email", "created_at")
    inlines = [CertificationInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not hasattr(obj, "trust_profile"):
            VendorTrustProfile.objects.create(vendor=obj)


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "solution_type")
    search_fields = ("name",)


# Filtering support in admin
list_filter = ["has_data_breach", "has_cyber_insurance"]
search_fields = ("vendor__name",)
