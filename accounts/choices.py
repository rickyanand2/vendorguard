# accounts/choices.py
"""Centralized enums (TextChoices) and constants for the accounts app."""

from django.db import models


class PlanChoices(models.TextChoices):
    """Subscription plans for `License.plan`."""

    STANDARD = "standard", "Standard"
    TEAMS = "teams", "Teams"
    ENTERPRISE = "enterprise", "Enterprise"


class MembershipRole(models.TextChoices):
    """RBAC roles for `Membership.role`."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class OrganizationStatus(models.TextChoices):
    """Lifecycle state for `Organization.status`."""

    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class AccessRuleAction(models.TextChoices):
    """Network policy action for `OrganizationAccessRule.action`."""

    ALLOW = "allow", "Allow"
    DENY = "deny", "Deny"


class AuthEventType(models.TextChoices):
    """Audit trail events for `AuthEvent.event`."""

    LOGIN_SUCCESS = "login_success", "Login Success"
    LOGIN_FAILED = "login_failed", "Login Failed"
    LOGOUT = "logout", "Logout"
    PASSWORD_RESET = "password_reset", "Password Reset"
    EMAIL_VERIFIED = "email_verified", "Email Verified"


# Public/free email domains blocked when a business email is required.
# Keep this list small and pragmatic; enforcement lives in services.
BLOCKED_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
    "live.com",
    "aol.com",
}
