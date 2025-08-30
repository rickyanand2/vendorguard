# Path: thirdparties/admin.py
# Purpose: Rich Django Admin for Third Parties with handy inlines and bulk actions.

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ThirdParty,
    ThirdPartyTrustProfile,
    ThirdPartyContact,
    ThirdPartyDomain,
    ThirdPartyEvidence,
    ThirdPartyService,
)

# ──────────────────────────────────────────────────────────────────────────────
# 🔧 Inline admin classes
#   - Keep related objects manageable directly from ThirdParty admin.
#   - Use TabularInline for compact lists; StackedInline for detailed/1-1.
# ──────────────────────────────────────────────────────────────────────────────


class TrustProfileInline(admin.StackedInline):
    """
    One-to-one inline for ThirdPartyTrustProfile.
    `fk_name` ensures Django links via third_party field.
    """

    model = ThirdPartyTrustProfile
    fk_name = "third_party"
    can_delete = False
    extra = 0
    fields = ("trust_score", "notes", "archived", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


class ContactInline(admin.TabularInline):
    model = ThirdPartyContact
    extra = 0
    fields = ("name", "email", "phone", "role", "is_primary")
    autocomplete_fields = ()
    show_change_link = True


class DomainInline(admin.TabularInline):
    model = ThirdPartyDomain
    extra = 0
    fields = ("domain",)
    show_change_link = True


class EvidenceInline(admin.TabularInline):
    model = ThirdPartyEvidence
    extra = 0
    fields = ("evidence_type", "title", "url", "issued_date", "expires_date")
    show_change_link = True


class ServiceInline(admin.TabularInline):
    model = ThirdPartyService
    extra = 0
    fields = ("name", "service_type", "data_sensitivity", "archived")
    show_change_link = True


# ──────────────────────────────────────────────────────────────────────────────
# 🧰 Shared actions
# ──────────────────────────────────────────────────────────────────────────────


@admin.action(description="Archive selected third parties")
def action_archive_thirdparties(modeladmin, request, queryset):
    queryset.update(archived=True)


@admin.action(description="Unarchive selected third parties")
def action_unarchive_thirdparties(modeladmin, request, queryset):
    queryset.update(archived=False)


@admin.action(description="Archive selected services")
def action_archive_services(modeladmin, request, queryset):
    queryset.update(archived=True)


@admin.action(description="Unarchive selected services")
def action_unarchive_services(modeladmin, request, queryset):
    queryset.update(archived=False)


# ──────────────────────────────────────────────────────────────────────────────
# 🏢 ThirdParty Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin.register(ThirdParty)
class ThirdPartyAdmin(admin.ModelAdmin):
    """
    Primary admin for suppliers.
    - Inlines: 1-1 Trust Profile + related contacts/domains/evidence/services
    - Bulk actions for archive/unarchive
    - Indexes/filters tuned for common TPRM flows
    """

    list_display = (
        "name",
        "organization",
        "lifecycle_status",
        "tier",
        "criticality",
        "risk_badge",
        "wf_state",
        "archived",
        "last_assessed",
        "next_review_due",
        "created_at",
    )
    list_filter = (
        "organization",
        "lifecycle_status",
        "tier",
        "criticality",
        "wf_state",
        "archived",
        "dpia_required",
        "processes_pii",
        "processes_pci",
        "processes_phi",
    )
    search_fields = (
        "name",
        "website",
        "description",
        "support_email",
        "security_contact_email",
    )
    autocomplete_fields = ("organization", "created_by")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("name",)
    actions = (action_archive_thirdparties, action_unarchive_thirdparties)

    # Helpful grouping for clarity
    fieldsets = (
        ("Identity", {"fields": ("organization", "name", "website", "description")}),
        (
            "Business Posture & Risk",
            {
                "fields": (
                    "lifecycle_status",
                    "tier",
                    "criticality",
                    "risk_snapshot",
                    ("last_assessed", "next_review_due"),
                    "dpia_required",
                    ("processes_pii", "processes_pci", "processes_phi"),
                )
            },
        ),
        (
            "Security Contacts",
            {
                "fields": (
                    "support_email",
                    "security_contact_email",
                    "security_portal_url",
                )
            },
        ),
        ("Workflow & Lifecycle", {"fields": ("wf_state", "archived", "tenant_id")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    inlines = [
        TrustProfileInline,
        ContactInline,
        DomainInline,
        EvidenceInline,
        ServiceInline,
    ]

    # Pretty badge for risk_snapshot
    @admin.display(description="Risk")
    def risk_badge(self, obj: ThirdParty):
        val = obj.risk_snapshot or 0
        color = (
            "#198754"
            if val < 34  # green
            else "#fd7e14" if val < 67 else "#dc3545"  # orange  # red
        )
        return format_html(
            '<span style="padding:2px 8px;border-radius:12px;background:{};color:#fff;">{}</span>',
            color,
            val,
        )


# ──────────────────────────────────────────────────────────────────────────────
# 🧪 Trust Profile Admin (optional direct registration)
#   - You can edit trust inline under ThirdParty, but direct admin can help bulk ops.
# ──────────────────────────────────────────────────────────────────────────────
@admin.register(ThirdPartyTrustProfile)
class ThirdPartyTrustProfileAdmin(admin.ModelAdmin):
    list_display = ("third_party", "trust_score", "archived", "updated_at")
    list_filter = ("archived",)
    search_fields = ("third_party__name",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("third_party",)
    ordering = ("-updated_at",)


# ──────────────────────────────────────────────────────────────────────────────
# 👥 Contact Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin.register(ThirdPartyContact)
class ThirdPartyContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "role", "third_party", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("name", "email", "role", "third_party__name")
    autocomplete_fields = ("third_party",)
    ordering = ("third_party__name", "name")


# ──────────────────────────────────────────────────────────────────────────────
# 🌐 Domain Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin.register(ThirdPartyDomain)
class ThirdPartyDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "third_party")
    search_fields = ("domain", "third_party__name")
    autocomplete_fields = ("third_party",)
    ordering = ("third_party__name", "domain")


# ──────────────────────────────────────────────────────────────────────────────
# 📄 Evidence Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin.register(ThirdPartyEvidence)
class ThirdPartyEvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "third_party",
        "evidence_type",
        "issued_date",
        "expires_date",
    )
    list_filter = ("evidence_type",)
    search_fields = ("title", "third_party__name", "notes")
    autocomplete_fields = ("third_party",)
    ordering = ("third_party__name", "-issued_date")


# ──────────────────────────────────────────────────────────────────────────────
# 🧰 Service Admin
# ──────────────────────────────────────────────────────────────────────────────
@admin.register(ThirdPartyService)
class ThirdPartyServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "third_party",
        "service_type",
        "data_sensitivity",
        "archived",
        "created_at",
    )
    list_filter = (
        "service_type",
        "data_sensitivity",
        "archived",
        "processes_pii",
        "processes_pci",
        "processes_phi",
    )
    search_fields = ("name", "third_party__name", "description")
    autocomplete_fields = ("third_party",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    actions = (action_archive_services, action_unarchive_services)
