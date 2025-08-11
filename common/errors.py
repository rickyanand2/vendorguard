"""Shared domain exceptions (cross-app)."""

from django.core.exceptions import PermissionDenied


class BusinessRuleError(Exception):
    """Generic business rule failure."""


class AlreadyMember(BusinessRuleError):
    """User already in organization."""


class DuplicateInvite(BusinessRuleError):
    """Duplicate pending invite exists."""


class InvalidInvite(BusinessRuleError):
    """Invite token invalid/expired."""


class InvalidToken(BusinessRuleError):
    """Verification/reset token invalid."""


class LastOwnerRemovalError(BusinessRuleError):
    """Would remove last owner."""


class InvalidEmailDomain(BusinessRuleError):
    """Non-business email rejected."""


class LicenseExpired(PermissionDenied):
    """License not current."""


class LockedOut(PermissionDenied):
    """Account temporarily locked."""


class MFARequired(PermissionDenied):
    """MFA required by policy."""


class IPAccessDenied(PermissionDenied):
    """IP blocked by policy."""
