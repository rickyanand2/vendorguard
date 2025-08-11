"""Accounts services (functional): registration, invites, membership, auth & policy."""

from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

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
import common.errors as ERR

logger = logging.getLogger(__name__)

# ========= helpers =============================================================


def _now():
    """Current timezone-aware datetime."""
    return timezone.now()


def extract_domain(email: str) -> str:
    """Return domain part of email."""
    return email.split("@", 1)[1].lower()


def is_blocked_domain(domain: str) -> bool:
    """True if public/free domain."""
    return domain in CH.BLOCKED_EMAIL_DOMAINS


def is_email_allowed_for_org(email: str, org: Organization) -> bool:
    """Business email allowed by org policy."""
    domain = extract_domain(email)
    if org.enforce_business_email and is_blocked_domain(domain):
        return False
    if org.domain:
        return domain == org.domain.lower()
    return True


def build_absolute(request, path: str) -> str:
    """Absolute URL for a path."""
    return request.build_absolute_uri(path)


# ========= membership ==========================================================


@transaction.atomic
def membership_add_member(
    user: CustomUser,
    org: Organization,
    role: str = CH.MembershipRole.MEMBER,
    make_primary: bool = False,
) -> Membership:
    """Add user to org; set primary if none exists or requested."""
    if Membership.objects.filter(user=user, organization=org, is_active=True).exists():
        raise ERR.AlreadyMember("User is already a member of this organization.")
    m = Membership.objects.create(
        user=user, organization=org, role=role, is_active=True
    )
    has_other_active = (
        Membership.objects.filter(user=user, is_active=True).exclude(pk=m.pk).exists()
    )
    if make_primary or not has_other_active:
        Membership.objects.filter(user=user, is_primary=True).update(is_primary=False)
        m.is_primary = True
        m.save(update_fields=["is_primary"])
    return m


@transaction.atomic
def membership_remove_member(actor: CustomUser, membership: Membership) -> None:
    """Deactivate membership; protect last owner."""
    org = membership.organization
    if membership.role == CH.MembershipRole.OWNER:
        owners = Membership.objects.filter(
            organization=org, role=CH.MembershipRole.OWNER, is_active=True
        )
        if owners.count() <= 1 and membership.user_id == actor.id:
            raise ERR.LastOwnerRemovalError(
                "You cannot remove the last remaining owner."
            )
    membership.is_active = False
    membership.is_primary = False
    membership.save(update_fields=["is_active", "is_primary"])


@transaction.atomic
def membership_change_role(membership: Membership, new_role: str) -> Membership:
    """Change role; ensure org keeps at least one owner."""
    if (
        membership.role == CH.MembershipRole.OWNER
        and new_role != CH.MembershipRole.OWNER
    ):
        others = Membership.objects.filter(
            organization=membership.organization,
            role=CH.MembershipRole.OWNER,
            is_active=True,
        ).exclude(pk=membership.pk)
        if not others.exists():
            raise ERR.LastOwnerRemovalError(
                "Organization must have at least one owner."
            )
    membership.role = new_role
    membership.save(update_fields=["role"])
    return membership


def membership_primary_org(user: CustomUser) -> Optional[Organization]:
    """Return user's primary org (or first active org)."""
    m = (
        user.memberships.filter(is_active=True, is_primary=True)
        .select_related("organization")
        .first()
    )
    if m:
        return m.organization
    any_m = (
        user.memberships.filter(is_active=True).select_related("organization").first()
    )
    return any_m.organization if any_m else None


# ========= registration ========================================================


@transaction.atomic
def registration_register_solo_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    job_title: Optional[str] = None,
) -> CustomUser:
    """Create personal org + owner membership + user."""
    domain = extract_domain(email)
    org = Organization.objects.create(
        name=f"{first_name}'s Workspace",
        is_personal=True,
        domain=domain,
        is_active=True,
    )
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        job_title=job_title,
        is_active=True,
    )
    membership_add_member(
        user=user, org=org, role=CH.MembershipRole.OWNER, make_primary=True
    )
    return user


@transaction.atomic
def registration_register_team_owner(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    org_name: str,
    domain: Optional[str] = None,
    job_title: Optional[str] = None,
) -> CustomUser:
    """Create team org + owner membership + user."""
    domain = domain or extract_domain(email)
    org = Organization.objects.create(
        name=org_name, is_personal=False, domain=domain, is_active=True
    )
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        job_title=job_title,
        is_active=True,
    )
    membership_add_member(
        user=user, org=org, role=CH.MembershipRole.OWNER, make_primary=True
    )
    return user


def registration_guarded_solo(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    job_title: Optional[str] = None,
) -> CustomUser:
    """Solo registration with business email enforcement."""
    domain = extract_domain(email)
    if is_blocked_domain(domain):
        raise ERR.InvalidEmailDomain("Personal/free email domains are not allowed.")
    return registration_register_solo_user(
        email, password, first_name, last_name, job_title
    )


def registration_guarded_team_owner(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    org_name: str,
    domain: Optional[str] = None,
    job_title: Optional[str] = None,
) -> CustomUser:
    """Team registration with business email enforcement."""
    if domain is None:
        domain = extract_domain(email)
    if is_blocked_domain(domain):
        raise ERR.InvalidEmailDomain(
            "Personal/free email domains are not allowed for team registration."
        )
    return registration_register_team_owner(
        email, password, first_name, last_name, org_name, domain, job_title
    )


# ========= invites =============================================================


def _invite_assert_email_allowed(email: str, org: Organization) -> None:
    """Raise if email violates org policy."""
    if not is_email_allowed_for_org(email, org):
        raise ERR.InvalidEmailDomain(
            "Only business emails matching your organization domain are allowed."
        )


def _invite_assert_not_duplicate(email: str, org: Organization) -> None:
    """Raise if a pending invite already exists."""
    exists = Invite.objects.filter(
        email=email, organization=org, is_expired=False, accepted_at__isnull=True
    ).exists()
    if exists:
        raise ERR.DuplicateInvite("An invite has already been sent to this email.")


def _invite_assert_not_member(email: str, org: Organization) -> None:
    """Raise if user already a member."""
    if CustomUser.objects.filter(
        email=email, memberships__organization=org, memberships__is_active=True
    ).exists():
        raise ERR.AlreadyMember("This user is already a member of the organization.")


@transaction.atomic
def invite_create(
    email: str, org: Organization, role: str = CH.MembershipRole.MEMBER
) -> Invite:
    """Create a new invite."""
    _invite_assert_email_allowed(email, org)
    _invite_assert_not_member(email, org)
    _invite_assert_not_duplicate(email, org)
    token = get_random_string(64)
    return Invite.objects.create(
        email=email, organization=org, role=role, token=token, is_expired=False
    )


def invite_build_link(invite: Invite, request) -> str:
    """Return absolute invite URL for this token."""
    return build_absolute(
        request, reverse("accounts:accept_invite") + f"?token={invite.token}"
    )


def invite_send(invite: Invite) -> None:
    """Send invite email (console backend in dev)."""
    try:
        send_mail(
            subject="You're invited",
            message=f"You've been invited to join {invite.organization.name}. Use your invite link.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[invite.email],
            fail_silently=True,
        )
    except Exception:  # pragma: no cover
        logger.exception("Failed to send invite email")


@transaction.atomic
def invite_accept(
    token: str, password: str, first_name: str = "", last_name: str = ""
) -> CustomUser:
    """Accept invite by token; create user and membership."""
    try:
        invite = Invite.objects.select_for_update().get(token=token)
    except Invite.DoesNotExist:
        raise ERR.InvalidInvite("Invalid invite token.")
    now = _now()
    if (
        invite.is_expired
        or invite.accepted_at is not None
        or now > invite.created_at + timezone.timedelta(days=CH.INVITE_EXPIRY_DAYS)
    ):
        raise ERR.InvalidInvite("This invite has expired or is no longer valid.")
    if CustomUser.objects.filter(email=invite.email).exists():
        raise ERR.BusinessRuleError("A user with this email already exists.")
    user = CustomUser.objects.create_user(
        email=invite.email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )
    membership_add_member(
        user=user, org=invite.organization, role=invite.role, make_primary=True
    )
    invite.accepted_at = now
    invite.save(update_fields=["accepted_at"])
    return user


def invite_expire_stale(days: int = CH.INVITE_EXPIRY_DAYS) -> int:
    """Expire invites older than N days (returns count updated)."""
    cutoff = _now() - timezone.timedelta(days=days)
    qs = Invite.objects.filter(
        accepted_at__isnull=True, is_expired=False, created_at__lte=cutoff
    )
    return qs.update(is_expired=True)


# ========= auth & policy =======================================================


def auth_log_event(
    user: CustomUser, event: str, *, ip: Optional[str] = None, ua: str = ""
) -> None:
    """Write an auth event."""
    AuthEvent.objects.create(user=user, event=event, ip=ip, user_agent=ua[:255])


def auth_evaluate_ip_access(org: Optional[Organization], ip: Optional[str]) -> None:
    """Deny/allow by org CIDR rules (deny-wins)."""
    if not org or not ip:
        return
    rules = OrganizationAccessRule.objects.filter(organization=org, is_active=True)
    if not rules.exists():
        return
    from ipaddress import ip_address, ip_network

    def _match(_ip: str, cidr: str) -> bool:
        try:
            return ip_address(_ip) in ip_network(cidr, strict=False)
        except Exception:
            return False

    any_deny = any(
        _match(ip, r.cidr) for r in rules if r.action == CH.AccessRuleAction.DENY
    )
    if any_deny:
        raise ERR.IPAccessDenied(
            "Access from your IP is not allowed for this organization."
        )
    allows = [r for r in rules if r.action == CH.AccessRuleAction.ALLOW]
    if allows and not any(_match(ip, r.cidr) for r in allows):
        raise ERR.IPAccessDenied(
            "Access from your IP is not allowed for this organization."
        )


@transaction.atomic
def auth_record_failed_login(
    user: CustomUser, org: Optional[Organization] = None
) -> None:
    """Bump lockout counters; set locked_until if over threshold."""
    org = org or membership_primary_org(user)
    max_attempts = (
        getattr(org, "max_failed_logins", CH.SECURITY_DEFAULTS["max_failed_logins"])
        if org
        else CH.SECURITY_DEFAULTS["max_failed_logins"]
    )
    lock_minutes = (
        getattr(org, "lockout_minutes", CH.SECURITY_DEFAULTS["lockout_minutes"])
        if org
        else CH.SECURITY_DEFAULTS["lockout_minutes"]
    )
    user.failed_login_count += 1
    if user.failed_login_count >= int(max_attempts):
        user.locked_until = _now() + timezone.timedelta(minutes=int(lock_minutes))
    user.save(update_fields=["failed_login_count", "locked_until"])


@transaction.atomic
def auth_record_successful_login(
    user: CustomUser, *, ip: Optional[str] = None, ua: str = ""
) -> None:
    """Reset lock counters and log success."""
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_ip = ip
    user.save(update_fields=["failed_login_count", "locked_until", "last_login_ip"])
    auth_log_event(user, CH.AuthEventType.LOGIN_SUCCESS, ip=ip, ua=ua)


def auth_guard_login_attempt(user: CustomUser, *, ip: Optional[str], ua: str) -> None:
    """Run pre-login checks: IP, lockout, org MFA (license hook later)."""
    org = membership_primary_org(user)
    auth_evaluate_ip_access(org, ip)
    if user.locked_until and _now() < user.locked_until:
        raise ERR.LockedOut(
            "Your account is temporarily locked. Please try again later."
        )
    if (org and org.require_mfa) and not user.mfa_enabled:
        raise ERR.MFARequired("Multi-factor authentication is required to sign in.")


# ========= email verify & password reset ======================================


def email_issue_token(user: CustomUser) -> str:
    """Create email verification token and return it."""
    token = get_random_string(64)
    EmailVerificationToken.objects.create(user=user, token=token)
    return token


@transaction.atomic
def email_verify(token: str) -> CustomUser:
    """Verify email by token."""
    try:
        t = EmailVerificationToken.objects.select_for_update().get(token=token)
    except EmailVerificationToken.DoesNotExist:
        raise ERR.InvalidToken("Invalid verification token.")
    if t.used_at is not None or _now() > t.created_at + timezone.timedelta(
        minutes=CH.EMAIL_VERIFICATION_EXPIRY_MINUTES
    ):
        raise ERR.InvalidToken("Verification token expired or already used.")
    user = t.user
    user.is_verified_email = True
    user.email_verified_at = _now()
    user.save(update_fields=["is_verified_email", "email_verified_at"])
    t.used_at = _now()
    t.save(update_fields=["used_at"])
    auth_log_event(user, CH.AuthEventType.EMAIL_VERIFIED)
    return user


def password_issue_reset(user: CustomUser) -> str:
    """Create password reset token and return it."""
    token = get_random_string(64)
    PasswordResetToken.objects.create(user=user, token=token)
    return token


@transaction.atomic
def password_reset_with_token(token: str, new_password: str) -> CustomUser:
    """Reset password using token."""
    try:
        t = PasswordResetToken.objects.select_for_update().get(token=token)
    except PasswordResetToken.DoesNotExist:
        raise ERR.InvalidToken("Invalid reset token.")
    if t.used_at is not None or _now() > t.created_at + timezone.timedelta(
        hours=CH.PASSWORD_RESET_EXPIRY_HOURS
    ):
        raise ERR.InvalidToken("Reset token expired or already used.")
    user = t.user
    user.set_password(new_password)
    user.last_password_change = _now()
    user.save(update_fields=["password", "last_password_change"])
    t.used_at = _now()
    t.save(update_fields=["used_at"])
    auth_log_event(user, CH.AuthEventType.PASSWORD_CHANGE)
    return user
