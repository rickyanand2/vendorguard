# services/accounts.py

import logging
from django.utils import timezone
from accounts.models import CustomUser, Organization, Membership, License
from accounts.constants import BLOCKED_EMAIL_DOMAINS
from django.utils.crypto import get_random_string
from accounts.models import Invite
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


# ====================================================================
# 🧠 Registration & Account Logic
# ====================================================================
class RegistrationService:

    # ----------------------------------------
    # Utility Methods:
    # ----------------------------------------

    # Get user’s org (safe default)
    @staticmethod
    def get_user_organization(user: CustomUser) -> Organization | None:
        try:
            membership = Membership.objects.select_related("organization").get(
                user=user
            )
            return membership.organization
        except Membership.DoesNotExist:
            return None

    # Extract domain
    @staticmethod
    def extract_domain(email: str) -> str:
        return email.split("@")[1].lower()

    # Validate if domain is blocked (i.e. public/free)
    @classmethod
    def is_blocked_domain(cls, domain: str) -> bool:
        return domain in BLOCKED_EMAIL_DOMAINS

    # Validate business email
    @classmethod
    def is_invalid_business_email(cls, email: str) -> bool:
        return cls.is_blocked_domain(cls.extract_domain(email))

    # Validate Email allowed in org
    @classmethod
    def is_email_allowed_for_org(cls, email: str, org: Organization) -> bool:
        domain = cls.extract_domain(email)
        return not cls.is_blocked_domain(domain) and (org.domain == domain)

    # ----------------------------------------
    # Registration Methods:
    # ----------------------------------------

    # Registers a single user with personal workspace.
    @classmethod
    def register_solo_user(
        cls, email, password, first_name, last_name, job_title=None
    ) -> CustomUser:

        domain = cls.extract_domain(email)
        # Create personal org
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

        Membership.objects.create(user=user, organization=org, role="owner")
        cls._create_trial_license(org, plan="standard")
        return user

    # Registers a team owner and creates new organization
    @classmethod
    def register_team_owner(
        cls,
        email,
        password,
        first_name,
        last_name,
        org_name,
        domain=None,
        job_title=None,
    ) -> CustomUser:
        domain = domain or cls.extract_domain(email)

        org = Organization.objects.create(
            name=org_name,
            is_personal=False,
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

        Membership.objects.create(user=user, organization=org, role="owner")
        cls._create_trial_license(org, plan="teams")

        return user

    # ------------------------------------------------------
    # License & Upgrade Logic
    # ------------------------------------------------------

    # Creates a 14-day trial license for the organization
    @staticmethod
    def _create_trial_license(org: Organization, plan: str) -> None:
        License.objects.create(
            organization=org,
            plan=plan,
            is_trial=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=14),
        )

    # Upgrade - Converts a personal organization into a team plan.
    @classmethod
    def upgrade_user_to_team(cls, user: CustomUser, new_org_name=None) -> Organization:
        membership = Membership.objects.get(user=user, role="owner")
        org = membership.organization

        if not org.is_personal:
            raise ValueError("Only personal accounts can be upgraded to team plans.")

        license = License.objects.filter(organization=org).first()
        if license:
            license.plan = "teams"
            license.is_trial = False
            license.save()

        org.name = new_org_name or f"{user.get_full_name()}'s Team"
        org.is_personal = False
        org.save()

        logger.info(f"User {user.email} upgraded to team plan")
        return org

    # ------------------------------------------------------
    # Invite Logic
    # ------------------------------------------------------
    @classmethod
    def invite_user_to_organization(
        cls, email: str, job_title: str, org: Organization
    ) -> str:
        """
        Sends an invite to a user by creating an Invite entry with a token.
        Returns the invite link.
        Raises ValueError if checks fail.
        """

        # Validate email domain
        if not cls.is_email_allowed_for_org(email, org):
            raise ValueError(
                "Only business emails matching your organization domain are allowed."
            )

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            raise ValueError("A user with this email already exists.")

        # Check for duplicate invites
        if Invite.objects.filter(
            email=email, organization=org, is_expired=False, accepted_at__isnull=True
        ).exists():
            raise ValueError("An invite has already been sent to this email.")

        # Create Invite
        token = get_random_string(length=64)
        Invite.objects.create(
            email=email,
            organization=org,
            role="member",
            token=token,
            is_expired=False,
        )

        return token


class InviteService:
    @staticmethod
    def create_invite(email, organization, role="member") -> Invite:
        token = get_random_string(64)
        invite = Invite.objects.create(
            email=email,
            organization=organization,
            role=role,
            token=token,
            is_expired=False,
        )
        return invite

    @staticmethod
    def generate_invite_link(invite, request) -> str:
        return request.build_absolute_uri(
            reverse("accounts:accept_invite") + f"?token={invite.token}"
        )

    @classmethod
    def send_invite(cls, email, job_title, org, request) -> Invite:
        # Centralized logic with validation + logging
        if not RegistrationService.is_email_allowed_for_org(email, org):
            raise ValidationError(
                "Only business emails matching your organization domain are allowed."
            )

        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")

        if Invite.objects.filter(
            email=email, organization=org, is_expired=False, accepted_at__isnull=True
        ).exists():
            raise ValidationError("An invite has already been sent to this email.")

        invite = cls.create_invite(email=email, organization=org)
        invite_link = cls.generate_invite_link(invite, request)
        logger.info(f"[InviteService] Invite link: {invite_link}")
        return invite

    @staticmethod
    def accept_invite(token, password, first_name="", last_name="") -> CustomUser:
        try:
            invite = Invite.objects.get(token=token)
        except Invite.DoesNotExist:
            raise ValueError("Invalid invite token.")

        if not invite.is_valid:
            raise ValueError("This invite has expired or is no longer valid.")

        if CustomUser.objects.filter(email=invite.email).exists():
            raise ValueError("A user with this email already exists.")

        # Create user
        user = CustomUser.objects.create_user(
            email=invite.email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        @staticmethod
        def expire_old_invites():
            expiration_threshold = timezone.now() - timedelta(days=7)
            Invite.objects.filter(
                accepted_at__isnull=True,
                is_expired=False,
                created_at__lte=expiration_threshold,
            ).update(is_expired=True)

        Membership.objects.create(
            user=user, organization=invite.organization, role=invite.role
        )

        invite.accepted_at = timezone.now()
        invite.save()
        return user
