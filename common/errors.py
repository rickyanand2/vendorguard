# common/errors.py
"""Shared exception types used across apps."""


class BusinessRuleError(Exception):
    """Generic business rule violation."""


class InvalidEmailDomain(BusinessRuleError):
    """Email domain not allowed (free domain or org mismatch)."""


class DuplicateInvite(BusinessRuleError):
    """An active invite already exists for this email & org."""


class AlreadyMember(BusinessRuleError):
    """User already exists and is a member of the org."""


class InvalidInvite(BusinessRuleError):
    """Invite token invalid or expired."""


class InvalidToken(BusinessRuleError):
    """Verification/reset token invalid or expired."""


class LastOwnerRemovalError(BusinessRuleError):
    """Refuse action that would leave org with no owner."""


class LockedOut(BusinessRuleError):
    """User temporarily locked due to failed attempts."""


class MFARequired(BusinessRuleError):
    """Org requires MFA but user doesn't have it enabled."""


class IPAccessDenied(BusinessRuleError):
    """Login IP not allowed by org access rules."""
