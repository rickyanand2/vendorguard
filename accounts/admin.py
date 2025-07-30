from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomSoloUserCreationForm, CustomUserChangeForm
from .models import CustomUser, License, Membership, Organization


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomSoloUserCreationForm
    form = CustomUserChangeForm

    list_display = ("email", "first_name", "last_name", "is_active", "is_admin")
    list_filter = ("is_admin", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "job_title",
                    "phone",
                    "address",
                    "state",
                    "country",
                )
            },
        ),
        (
            "Permissions",
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
                ),
            },
        ),
    )

    search_fields = ("email",)
    ordering = ("email",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "is_personal")
    search_fields = ("name", "domain")
    list_filter = ("is_personal",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")
    list_filter = ("role",)


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("organization", "plan", "is_trial", "start_date", "end_date")
    list_filter = ("plan", "is_trial")
