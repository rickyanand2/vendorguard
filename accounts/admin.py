# accounts/admin.py
"""Admin bindings for accounts (email-as-username) with Organization management from User admin."""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from accounts import choices as CH
from .models import (
    AuthEvent,
    CustomUser,
    EmailVerificationToken,
    Invite,
    License,
    Membership,
    Organization,
    OrganizationAccessRule,
    PasswordResetToken,
    RecoveryCode,
)


# ──────────────────────────────────────────────────────────────────────────────
# Utilities for linking a user to an Organization via Membership
# ──────────────────────────────────────────────────────────────────────────────


def _set_primary_membership(user: CustomUser, org: Organization) -> None:
    """
    Make `org` the user's primary Organization, creating/updating Membership safely.
    Ensures:
      - exactly one active, primary membership per user (enforced both in code and by DB constraint)
      - membership is created if it doesn't exist, set active & primary
      - any other primary memberships are demoted
    """
    # Demote any other primary memberships
    (
        Membership.objects.filter(user=user, is_active=True, is_primary=True)
        .exclude(organization=org)
        .update(is_primary=False)
    )

    # Upsert membership for the selected org
    m, created = Membership.objects.get_or_create(
        user=user,
        organization=org,
        defaults={
            "role": CH.MembershipRole.MEMBER,
            "is_active": True,
            "is_primary": True,
        },
    )
    if not created:
        changed = False
        if not m.is_active:
            m.is_active = True
            changed = True
        if not m.is_primary:
            m.is_primary = True
            changed = True
        if changed:
            m.save(update_fields=["is_active", "is_primary"])


# ──────────────────────────────────────────────────────────────────────────────
# Forms (add a synthetic "primary_organization" field to User admin forms)
# ──────────────────────────────────────────────────────────────────────────────


class AdminUserCreationForm(UserCreationForm):
    """Create user via admin (with optional primary org selection)."""

    primary_organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        help_text=_(
            "Optional: set the user's primary organization (creates membership)."
        ),
        label=_("Primary organization"),
    )

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "primary_organization")


class AdminUserChangeForm(UserChangeForm):
    """Edit user via admin (with primary org selector)."""

    primary_organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        help_text=_("Set or change the user's primary organization."),
        label=_("Primary organization"),
    )

    class Meta:
        model = CustomUser
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill current primary organization using the model property
        if self.instance and self.instance.pk:
            current_org = getattr(self.instance, "organization", None)
            if current_org:
                self.fields["primary_organization"].initial = current_org


# ──────────────────────────────────────────────────────────────────────────────
# Inlines
# ──────────────────────────────────────────────────────────────────────────────


class MembershipInlineForUser(admin.TabularInline):
    """
    Inline memberships under the User:
    lets admins see/add all org relationships, and mark one as primary.
    DB unique constraints will enforce only one active+primary per user.
    """

    model = Membership
    extra = 0
    autocomplete_fields = ("organization",)
    fields = (
        "organization",
        "role",
        "is_active",
        "is_primary",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-is_primary", "organization__name")


class MembershipInlineForOrg(admin.TabularInline):
    """Inline members under an Organization."""

    model = Membership
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user", "role", "is_active", "is_primary", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-is_primary", "user__email")


# ──────────────────────────────────────────────────────────────────────────────
# CustomUser admin
# ──────────────────────────────────────────────────────────────────────────────


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Email-as-username user admin with organization membership controls."""

    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    model = CustomUser
    inlines = [MembershipInlineForUser]

    # Show current primary org in list display for quick scanning
    def organization_name(self, obj: CustomUser):
        org = getattr(obj, "organization", None)
        return getattr(org, "name", "—")

    organization_name.short_description = _("Organization")

    list_display = (
        "email",
        "first_name",
        "last_name",
        "organization_name",
        "is_active",
        "is_admin",
        "date_joined",
    )
    list_filter = ("is_active", "is_admin", "is_superuser")
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "memberships__organization__name",
    )
    ordering = ("email",)
    readonly_fields = (
        "date_joined",
        "last_login",
        "email_verified_at",
        "last_password_change",
        "locked_until",
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "job_title",
                    "phone",
                    "address",
                    "state",
                    "country",
                    "is_verified_email",
                    "email_verified_at",
                    "mfa_enabled",
                )
            },
        ),
        (
            _("Organization & Membership"),
            {
                "description": _(
                    "Pick a primary organization here. Use the Memberships inline below for advanced control."
                ),
                "fields": ("primary_organization",),
            },
        ),
        (
            _("Security state"),
            {
                "fields": (
                    "failed_login_count",
                    "locked_until",
                    "last_login_ip",
                    "last_password_change",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_admin",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "primary_organization",
                    "is_active",
                    "is_admin",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")

    # Hook to apply primary_organization on save (create & update)
    def save_model(self, request, obj: CustomUser, form, change):
        super().save_model(request, obj, form, change)
        org = form.cleaned_data.get("primary_organization")
        if org:
            _set_primary_membership(obj, org)


# ──────────────────────────────────────────────────────────────────────────────
# Organization admin
# ──────────────────────────────────────────────────────────────────────────────


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Manage organizations; includes member inline and quick stats."""

    list_display = (
        "name",
        "domain",
        "status",
        "is_active",
        "require_mfa",
        "member_count",
    )
    list_filter = ("status", "is_active", "require_mfa")
    search_fields = ("name", "domain")
    ordering = ("name",)
    inlines = [MembershipInlineForOrg]

    def member_count(self, obj: Organization) -> int:
        return obj.memberships.filter(is_active=True).count()

    member_count.short_description = _("Active members")


# ──────────────────────────────────────────────────────────────────────────────
# Membership admin (kept for power users; inline usually suffices)
# ──────────────────────────────────────────────────────────────────────────────


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "organization",
        "role",
        "is_active",
        "is_primary",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_primary")
    search_fields = ("user__email", "organization__name")
    autocomplete_fields = ("user", "organization")
    ordering = ("organization__name", "user__email")


# ──────────────────────────────────────────────────────────────────────────────
# Remaining admin bindings (unchanged)
# ──────────────────────────────────────────────────────────────────────────────


@admin.register(OrganizationAccessRule)
class OrganizationAccessRuleAdmin(admin.ModelAdmin):
    list_display = ("organization", "action", "cidr", "is_active", "created_at")
    list_filter = ("action", "is_active")
    search_fields = ("organization__name", "cidr")
    autocomplete_fields = ("organization",)


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("organization", "plan", "start_date", "end_date", "is_trial")
    list_filter = ("plan", "is_trial")
    search_fields = ("organization__name",)
    autocomplete_fields = ("organization",)


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "organization",
        "role",
        "created_at",
        "accepted_at",
        "is_expired",
    )
    list_filter = ("role", "is_expired")
    search_fields = ("email", "organization__name")
    autocomplete_fields = ("organization", "invited_by")
    readonly_fields = ("created_at", "accepted_at")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "used_at")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "used_at")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "used_at")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "used_at")


@admin.register(RecoveryCode)
class RecoveryCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "used_at")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
    readonly_fields = ("used_at",)


@admin.register(AuthEvent)
class AuthEventAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "ip", "occurred_at")
    list_filter = ("event",)
    search_fields = ("user__email", "ip", "user_agent")
    autocomplete_fields = ("user",)
    readonly_fields = ("occurred_at",)
