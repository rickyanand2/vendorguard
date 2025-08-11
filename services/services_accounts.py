# services/services_accounts.py
"""Accounts domain services (function-based, no Django model business logic)."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

import common.errors as ERR
from accounts import choices as CH
from accounts.models import (
    AuthEvent,
    CustomUser,
    EmailVerificationToken,
    Invite,
    Membership,
    Organization,
    OrganizationAccessRule,
    PasswordResetToken,
)


# ===== Helpers =================================================================
def _extract_domain(email: str) -> str:
    """Return lowercase domain part of an email."""
    return (email or "").split("@")[-1].lower().strip()


def _is_blocked_domain(domain: str) -> bool:
    """True if domain is in the public/free blocklist."""
    return domain in CH.BLOCKED_EMAIL_DOMAINS


def _require_business_email(email: str, expected_domain: Optional[str] = None) -> None:
    """Validate that email is from a business domain and (optionally) matches expected."""
    domain = _extract_domain(email)
    if _is_blocked_domain(domain):
        raise ERR.InvalidEmailDomain(
            "Please use your business email (public domains are not allowed)."
        )
    if expected_domain and domain != expected_domain.lower():
        raise ERR.InvalidEmailDomain(
            "Email domain must match the organization's domain."
        )


def _ip_allowed_for_org(org: Organization, ip: Optional[str]) -> bool:
    """Evaluate org IP allow/deny rules against an IP string."""
    if not ip or not org.access_rules.filter(is_active=True).exists():
        return True  # no rule -> allow

    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False

    rules = list(org.access_rules.filter(is_active=True))
    # Deny wins
    for r in rules:
        try:
            cidr = ipaddress.ip_network(r.cidr, strict=False)
        except ValueError:
            continue
        if ip_obj in cidr and r.action == CH.AccessRuleAction.DENY:
            return False

    # If any ALLOW exists, IP must match at least one
    allows = [r for r in rules if r.action == CH.AccessRuleAction.ALLOW]
    if allows:
        for r in allows:
            try:
                cidr = ipaddress.ip_network(r.cidr, strict=False)
            except ValueError:
                continue
            if ip_obj in cidr:
                return True
        return False

    # Only DENYs exist and none matched -> allow
    return True


def membership_primary_org(user: CustomUser) -> Optional[Organization]:
    """Return user's primary org (or first active)."""
    m = (
        Membership.objects.select_related("organization")
        .filter(user=user, is_active=True, is_primary=True)
        .first()
        or Membership.objects.select_related("organization")
        .filter(user=user, is_active=True)
        .order_by("organization__name")
        .first()
    )
    return m.organization if m else None


# ===== Auth guards & audit =====================================================
def auth_guard_login_attempt(user: CustomUser, ip: Optional[str], ua: str = "") -> None:
    """Enforce lockout, MFA policy, and IP rules before allowing login."""
    # Locked out?
    now = timezone.now()
    if user.locked_until and user.locked_until > now:
        raise ERR.LockedOut("Too many failed attempts. Please try again later.")

    # Find org policy (use primary org if available)
    org = membership_primary_org(user)
    if org:
        # IP policy
        if not _ip_allowed_for_org(org, ip):
            raise ERR.IPAccessDenied("Your IP address is not allowed to sign in.")

        # MFA policy
        if org.require_mfa and not user.mfa_enabled:
            raise ERR.MFARequired(
                "This organization requires MFA. Please enable MFA to continue."
            )


def auth_record_successful_login(
    user: CustomUser, ip: Optional[str], ua: str = ""
) -> None:
    """Reset counters and record audit event."""
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_ip = ip
    user.save(update_fields=["failed_login_count", "locked_until", "last_login_ip"])

    AuthEvent.objects.create(
        user=user, event=CH.AuthEventType.LOGIN_SUCCESS, ip=ip, user_agent=ua
    )


def auth_record_failed_login(user: CustomUser) -> None:
    """Increment counters, possibly lock account, and record audit event."""
    # Get org policy knobs (fallbacks)
    org = membership_primary_org(user)
    max_fails = (org.max_failed_logins if org else 7) or 7
    lock_minutes = (org.lockout_minutes if org else 15) or 15

    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= max_fails:
        user.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
        user.failed_login_count = 0  # reset after lock

    user.save(update_fields=["failed_login_count", "locked_until"])
    AuthEvent.objects.create(user=user, event=CH.AuthEventType.LOGIN_FAILED)


# ===== Registration ============================================================
def _create_org(name: str, domain: str) -> Organization:
    """Create a business org (unique domain)."""
    return Organization.objects.create(
        name=name,
        is_personal=False,  # business service -> team orgs
        domain=domain.lower(),
        is_active=True,
    )


def _create_owner_membership(user: CustomUser, org: Organization) -> Membership:
    """Link user as owner to org."""
    return Membership.objects.create(
        user=user, organization=org, role=CH.MembershipRole.OWNER
    )


@transaction.atomic
def registration_guarded_solo(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    job_title: Optional[str] = None,
) -> CustomUser:
    """Register a 'solo' owner but still as a business org (unique domain)."""
    domain = _extract_domain(email)
    _require_business_email(email)
    # Create org (name can be domain-based or person-based)
    org = _create_org(name=f"{first_name} {last_name} ({domain})", domain=domain)

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        job_title=job_title,
        is_active=True,
    )
    _create_owner_membership(user, org)
    return user


@transaction.atomic
def registration_guarded_team_owner(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    org_name: str,
    domain: Optional[str] = None,
    job_title: Optional[str] = None,
) -> CustomUser:
    """Register team owner and create org with explicit/matched domain."""
    inferred = _extract_domain(email)
    target_domain = (domain or inferred).lower()
    _require_business_email(email, expected_domain=target_domain)

    org = _create_org(name=org_name, domain=target_domain)

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        job_title=job_title,
        is_active=True,
    )
    _create_owner_membership(user, org)
    return user


# ===== Email verification & password reset ====================================
TOKEN_TTL_MINUTES = 30  # 30-minute expiry


def email_issue_token(user: CustomUser) -> str:
    """Create a short-lived email verification token and return it (dev flow)."""
    token = get_random_string(48)
    EmailVerificationToken.objects.create(user=user, token=token)
    return token


def email_verify(token: str) -> None:
    """Verify email token within TTL; mark user verified."""
    try:
        rec = EmailVerificationToken.objects.select_related("user").get(token=token)
    except EmailVerificationToken.DoesNotExist:
        raise ERR.InvalidToken("Invalid or expired token.")

    if rec.used_at:
        raise ERR.InvalidToken("Token already used.")
    if timezone.now() - rec.created_at > timedelta(minutes=TOKEN_TTL_MINUTES):
        raise ERR.InvalidToken("Token expired. Please request a new one.")

    u = rec.user
    u.is_verified_email = True
    u.email_verified_at = timezone.now()
    u.save(update_fields=["is_verified_email", "email_verified_at"])

    rec.used_at = timezone.now()
    rec.save(update_fields=["used_at"])

    AuthEvent.objects.create(user=u, event=CH.AuthEventType.EMAIL_VERIFIED)


def password_issue_reset(user: CustomUser) -> str:
    """Create a short-lived password reset token (dev flow)."""
    token = get_random_string(48)
    PasswordResetToken.objects.create(user=user, token=token)
    return token


def password_reset_with_token(token: str, new_password: str) -> None:
    """Reset password if token is valid within TTL."""
    try:
        rec = PasswordResetToken.objects.select_related("user").get(token=token)
    except PasswordResetToken.DoesNotExist:
        raise ERR.InvalidToken("Invalid or expired token.")

    if rec.used_at:
        raise ERR.InvalidToken("Token already used.")
    if timezone.now() - rec.created_at > timedelta(minutes=TOKEN_TTL_MINUTES):
        raise ERR.InvalidToken("Token expired. Please request a new one.")

    u = rec.user
    u.set_password(new_password)
    u.last_password_change = timezone.now()
    u.save(update_fields=["password", "last_password_change"])

    rec.used_at = timezone.now()
    rec.save(update_fields=["used_at"])

    AuthEvent.objects.create(user=u, event=CH.AuthEventType.PASSWORD_RESET)


# ===== Invites ================================================================
def _ensure_not_member(email: str, org: Organization) -> None:
    """Raise AlreadyMember if user exists and is in org."""
    try:
        u = CustomUser.objects.get(email=email.lower())
    except CustomUser.DoesNotExist:
        return
    if Membership.objects.filter(user=u, organization=org, is_active=True).exists():
        raise ERR.AlreadyMember("This user is already a member of your organization.")


def invite_create(
    email: str, org: Organization, role: str = CH.MembershipRole.MEMBER
) -> Invite:
    """Validate and create an invite record."""
    email = email.lower().strip()
    # Domain policy
    if org.enforce_business_email:
        _require_business_email(
            email, expected_domain=org.domain or _extract_domain(email)
        )

    # Already a member?
    _ensure_not_member(email, org)

    # Duplicate invite?
    exists = Invite.objects.filter(
        email=email, organization=org, is_expired=False, accepted_at__isnull=True
    ).exists()
    if exists:
        raise ERR.DuplicateInvite("An active invitation already exists for this email.")

    token = get_random_string(64)
    return Invite.objects.create(
        email=email, organization=org, role=role, token=token, is_expired=False
    )


def invite_build_link(invite: Invite, request) -> str:
    """Build absolute accept-invite URL."""
    return request.build_absolute_uri(
        reverse("accounts:accept_invite") + f"?token={invite.token}"
    )


def invite_accept(
    token: str, password: str, first_name: str = "", last_name: str = ""
) -> CustomUser:
    """Accept invite, create user, and attach membership."""
    try:
        inv = Invite.objects.select_related("organization").get(token=token)
    except Invite.DoesNotExist:
        raise ERR.InvalidInvite("Invalid invite token.")

    # Validity window: 7 days (model property computed in UI; enforce here)
    if inv.is_expired:
        raise ERR.InvalidInvite("This invite has expired.")
    if inv.accepted_at:
        raise ERR.InvalidInvite("This invite has already been used.")

    # Ensure not already a member
    _ensure_not_member(inv.email, inv.organization)

    user = CustomUser.objects.create_user(
        email=inv.email,
        password=password,
        first_name=first_name or "",
        last_name=last_name or "",
        is_active=True,
    )
    Membership.objects.create(user=user, organization=inv.organization, role=inv.role)

    inv.accepted_at = timezone.now()
    inv.save(update_fields=["accepted_at"])

    return user


# ===== Membership maintenance =================================================
def membership_change_role(membership: Membership, new_role: str) -> None:
    """Change a member's role, preserving at least one OWNER."""
    # Prevent removing last owner
    if (
        membership.role == CH.MembershipRole.OWNER
        and new_role != CH.MembershipRole.OWNER
    ):
        owners = Membership.objects.filter(
            organization=membership.organization,
            role=CH.MembershipRole.OWNER,
            is_active=True,
        ).exclude(id=membership.id)
        if not owners.exists():
            raise ERR.LastOwnerRemovalError(
                "An organization must have at least one owner."
            )

    membership.role = new_role
    membership.save(update_fields=["role"])


def membership_remove_member(actor: CustomUser, membership: Membership) -> None:
    """Deactivate a member; refuse removing last owner."""
    if membership.role == CH.MembershipRole.OWNER:
        owners = Membership.objects.filter(
            organization=membership.organization,
            role=CH.MembershipRole.OWNER,
            is_active=True,
        ).exclude(id=membership.id)
        if not owners.exists():
            raise ERR.LastOwnerRemovalError(
                "An organization must have at least one owner."
            )

    membership.is_active = False
    membership.save(update_fields=["is_active"])
