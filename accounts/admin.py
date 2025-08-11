"""Admin bindings for accounts (email-as-username)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import (
    AuthEvent,
    CustomUser,
    EmailVerificationToken,
    Invite,
    Membership,
    Organization,
    OrganizationAccessRule,
    PasswordResetToken,
    RecoveryCode,
    License,
)


# ---------- Admin-only forms (do NOT use in views) ----------
class AdminUserCreationForm(UserCreationForm):
    """Create user via admin."""

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")


class AdminUserChangeForm(UserChangeForm):
    """Edit user via admin."""

    class Meta:
        model = CustomUser
        fields = "__all__"


# ---------- CustomUser admin ----------
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Email as username admin."""

    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    model = CustomUser

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_admin",
        "date_joined",
    )
    list_filter = ("is_active", "is_admin", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
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
                    "is_active",
                    "is_admin",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")


# ---------- Organization ----------
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "status", "is_active", "require_mfa")
    list_filter = ("status", "is_active", "require_mfa")
    search_fields = ("name", "domain")
    ordering = ("name",)


# ---------- Membership ----------
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


# ---------- Access rules ----------
@admin.register(OrganizationAccessRule)
class OrganizationAccessRuleAdmin(admin.ModelAdmin):
    list_display = ("organization", "action", "cidr", "is_active", "created_at")
    list_filter = ("action", "is_active")
    search_fields = ("organization__name", "cidr")
    autocomplete_fields = ("organization",)


# ---------- License ----------
@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("organization", "plan", "start_date", "end_date", "is_trial")
    list_filter = ("plan", "is_trial")
    search_fields = ("organization__name",)
    autocomplete_fields = ("organization",)


# ---------- Invites & tokens ----------
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
