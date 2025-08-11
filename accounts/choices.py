"""Enums (TextChoices) and constants for the accounts app (data-only)."""

from django.db import models

# ===== Enums =================================================================


class MembershipRole(models.TextChoices):
    """Organization membership roles."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class OrganizationStatus(models.TextChoices):
    """Organization lifecycle state."""

    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class AuthEventType(models.TextChoices):
    """Auth/audit event types."""

    LOGIN_SUCCESS = "login_success", "Login Success"
    LOGIN_FAILED = "login_failed", "Login Failed"
    LOGOUT = "logout", "Logout"
    PASSWORD_CHANGE = "password_change", "Password Change"
    MFA_ENABLED = "mfa_enabled", "MFA Enabled"
    MFA_DISABLED = "mfa_disabled", "MFA Disabled"
    EMAIL_VERIFIED = "email_verified", "Email Verified"


class AccessRuleAction(models.TextChoices):
    """Org network policy action."""

    ALLOW = "allow", "Allow"
    DENY = "deny", "Deny"


class PlanChoices(models.TextChoices):
    """Available subscription plans."""

    STANDARD = "standard", "Standard"
    TEAMS = "teams", "Teams"
    ENTERPRISE = "enterprise", "Enterprise"


# ===== Constants (no logic) ===================================================

BLOCKED_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
}

INVITE_EXPIRY_DAYS = 7
EMAIL_VERIFICATION_EXPIRY_MINUTES = 30
PASSWORD_RESET_EXPIRY_HOURS = 2

SECURITY_DEFAULTS = {
    "password_min_length": 12,
    "max_failed_logins": 7,
    "lockout_minutes": 15,
    "session_timeout_minutes": 60,
    "enforce_business_email": True,
}
