# accounts/choices.py
"""Central enums (TextChoices) and constants for the accounts app."""

from django.db import models


# =========================
# Enums (TextChoices)
# =========================
class MembershipRole(models.TextChoices):
    """Organization membership roles."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class PlanChoices(models.TextChoices):
    """Subscription plan tiers."""

    STANDARD = "standard", "Standard"
    TEAMS = "teams", "Teams"
    ENTERPRISE = "enterprise", "Enterprise"


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
    """Org network access policy action."""

    ALLOW = "allow", "Allow"
    DENY = "deny", "Deny"


# =========================
# Constants
# =========================
# Public/free email domains to block.
BLOCKED_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
}

# Token expiry windows (hours/days).
INVITE_EXPIRY_DAYS = 7
EMAIL_VERIFICATION_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 2

# Default org security knobs (used when unset).
SECURITY_DEFAULTS = {
    "password_min_length": 12,
    "max_failed_logins": 7,
    "lockout_minutes": 15,
    "session_timeout_minutes": 60,
    "enforce_business_email": True,
}
