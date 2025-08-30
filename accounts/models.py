"""Lean, data-only models for the accounts app (no business logic)."""

from ipaddress import ip_network

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Index, Q, UniqueConstraint
from django.utils import timezone

from accounts import choices as CH


# ===== User manager ===========================================================
class CustomUserManager(BaseUserManager):
    """Create/save users."""

    def create_user(
        self,
        email,
        first_name: str = "",
        last_name: str = "",
        password=None,
        **extra_fields,
    ):
        """Create regular user."""
        if not email:
            raise ValueError("Users must have a valid email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name or "",
            last_name=last_name or "",
            **extra_fields,
        )
        if password:
            user.set_password(password)  # hash password
        else:
            user.set_unusable_password()  # invite/verify flow
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        first_name: str = "Admin",
        last_name: str = "",
        password=None,
        **extra_fields,
    ):
        """Create superuser."""
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields,
        )
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ===== Organization ===========================================================
class Organization(models.Model):
    """Customer tenant container."""

    name = models.CharField(max_length=255, unique=True)
    is_personal = models.BooleanField(default=False)  # solo workspace flag
    domain = models.CharField(
        max_length=191, blank=True, null=True, help_text="Business email domain."
    )
    status = models.CharField(
        max_length=12,
        choices=CH.OrganizationStatus.choices,
        default=CH.OrganizationStatus.ACTIVE,
    )
    is_active = models.BooleanField(default=True)

    # Policy knobs (data-only; enforced in services/middleware)
    require_mfa = models.BooleanField(default=False)
    password_min_length = models.PositiveSmallIntegerField(default=12)
    max_failed_logins = models.PositiveSmallIntegerField(default=7)
    lockout_minutes = models.PositiveSmallIntegerField(default=15)
    session_timeout_minutes = models.PositiveSmallIntegerField(default=60)
    enforce_business_email = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)  # created timestamp
    updated_at = models.DateTimeField(auto_now=True)  # updated timestamp

    class Meta:
        indexes = [Index(fields=["name"]), Index(fields=["domain"])]
        constraints = [
            UniqueConstraint(
                fields=["domain"],
                name="uniq_org_domain_nullable",
                condition=Q(domain__isnull=False) & ~Q(domain=""),
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        """Readable label."""
        return self.name


# ===== Network policy (IP rules) =============================================
class OrganizationAccessRule(models.Model):
    """IP allow/deny CIDR rules."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="access_rules"
    )
    action = models.CharField(
        max_length=10,
        choices=CH.AccessRuleAction.choices,
        default=CH.AccessRuleAction.ALLOW,
    )
    cidr = models.CharField(max_length=64, help_text="CIDR, e.g., 203.0.113.0/24")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["organization", "is_active"])]

    def __str__(self):
        """Readable label."""
        return f"{self.organization.name} {self.action.upper()} {self.cidr}"

    def clean(self):
        """Validate CIDR value."""
        try:
            ip_network(self.cidr)
        except Exception as exc:
            raise ValidationError({"cidr": f"Invalid CIDR: {exc}"})


# ===== Custom user ============================================================
class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Application user (email login)."""

    email = models.EmailField(unique=True, max_length=255, db_index=True)
    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")

    # Profile
    job_title = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Email verification
    is_verified_email = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Security posture (data only)
    last_password_change = models.DateTimeField(null=True, blank=True)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # MFA footprint
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=64, blank=True, null=True)

    # Django admin + status
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def organization(self):
        """
        Return the user's active organization.
        Works whether you store org directly on user or via Membership.
        """
        # direct field on user (if you ever add one)
        org = getattr(self, "_organization", None)
        if org is not None:
            return org

        # via Membership (preferred multi-tenant pattern)
        try:
            from accounts.models import Membership  # local import to avoid cycles

            m = (
                Membership.objects.filter(user=self, is_active=True)
                .select_related("organization")
                .first()
            )
            return m.organization if m else None
        except Exception:
            return None

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        """Readable label."""
        return f"{self.full_name} <{self.email}>"

    @property
    def is_staff(self):
        """Django admin flag."""
        return self.is_admin

    @property
    def full_name(self) -> str:
        """Full name or email fallback."""
        fn = (self.first_name or "").strip()
        ln = (self.last_name or "").strip()
        return (fn + " " + ln).strip() or self.email


# ===== Membership (user↔org) ==================================================
class Membership(models.Model):
    """User membership in an organization."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=10,
        choices=CH.MembershipRole.choices,
        default=CH.MembershipRole.MEMBER,
    )
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(
        default=False, help_text="Default org when user has multiple orgs."
    )
    created_at = models.DateTimeField(auto_now_add=True)  # created timestamp
    updated_at = models.DateTimeField(auto_now=True)  # updated timestamp

    class Meta:
        indexes = [
            Index(fields=["organization", "role"]),
            Index(fields=["user", "is_active"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["user", "organization"],
                name="uniq_user_org_active",
                condition=Q(is_active=True),
            ),
            UniqueConstraint(
                fields=["user"],
                name="uniq_primary_membership_per_user",
                condition=Q(is_primary=True) & Q(is_active=True),
            ),
        ]
        ordering = ["organization__name", "user__email"]

    def __str__(self):
        """Readable label."""
        status = "active" if self.is_active else "inactive"
        return f"{self.user.email} [{self.role}] @ {self.organization.name} ({status})"


# ===== License (subscription) =================================================
class License(models.Model):
    """Subscription license record."""

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="license"
    )
    plan = models.CharField(
        max_length=20, choices=CH.PlanChoices.choices, default=CH.PlanChoices.STANDARD
    )
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    is_trial = models.BooleanField(default=True)

    class Meta:
        indexes = [Index(fields=["end_date"]), Index(fields=["plan"])]
        ordering = ["end_date"]

    def __str__(self):
        """Readable label."""
        return f"{self.organization.name} – {self.plan.capitalize()}"


# ===== Invites & short-lived tokens ==========================================
class Invite(models.Model):
    """Pending invitation to join an org."""

    email = models.EmailField()
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invites"
    )
    role = models.CharField(
        max_length=10,
        choices=CH.MembershipRole.choices,
        default=CH.MembershipRole.MEMBER,
    )
    token = models.CharField(
        max_length=64, unique=True, validators=[MinLengthValidator(32)]
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invites",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        indexes = [
            Index(fields=["email"]),
            Index(fields=["organization", "created_at"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["organization", "email"],
                name="uniq_pending_invite_per_email_org",
                condition=Q(accepted_at__isnull=True) & Q(is_expired=False),
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        """Readable label."""
        state = (
            "accepted"
            if self.accepted_at
            else ("expired" if self.is_expired else "pending")
        )
        return f"Invite {self.email} @ {self.organization.name} ({state})"


class EmailVerificationToken(models.Model):
    """Short-lived email verification token."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_tokens"
    )
    token = models.CharField(
        max_length=64, unique=True, validators=[MinLengthValidator(32)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [Index(fields=["user", "created_at"])]

    def __str__(self):
        """Readable label (non-sensitive token preview)."""
        preview = self.token[:6]
        return f"EmailVerifyToken({preview}…) for {self.user.email}"


class PasswordResetToken(models.Model):
    """Short-lived password reset token."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reset_tokens"
    )
    token = models.CharField(
        max_length=64, unique=True, validators=[MinLengthValidator(32)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [Index(fields=["user", "created_at"])]

    def __str__(self):
        """Readable label (non-sensitive token preview)."""
        preview = self.token[:6]
        return f"PasswordResetToken({preview}…) for {self.user.email}"


class RecoveryCode(models.Model):
    """MFA recovery code (hashed)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recovery_codes",
    )
    code_hash = models.CharField(max_length=128)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [Index(fields=["user"])]

    def __str__(self):
        """Readable label (do not show full hash)."""
        preview = (self.code_hash or "")[:8]
        return f"RecoveryCode({preview}…) for {self.user.email}"


# ===== Audit =================================================================
class AuthEvent(models.Model):
    """Auth/audit trail entry."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_events"
    )
    event = models.CharField(max_length=32, choices=CH.AuthEventType.choices)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["user", "occurred_at"])]
        ordering = ["-occurred_at"]

    def __str__(self):
        """Readable label."""
        return f"{self.user.email} {self.event} @ {self.occurred_at:%Y-%m-%d %H:%M:%S}"
