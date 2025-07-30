# accounts/models.py

from datetime import timedelta

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


# ======================================================================================
# USER MANAGER
# Custom user manager handles user and superuser creation || Overrides default user model
# ======================================================================================
class CustomUserManager(BaseUserManager):

    # Creates and saves a regular user with the given details.
    def create_user(
        self, email, first_name="", last_name=None, password=None, **extra_fields
    ):
        if not email:
            raise ValueError("Users must have a valid email address")

        email = self.normalize_email(email)

        # Create user object with provided fields
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )

        user.set_password(password)  # Hashes the password securely
        user.save(using=self._db)  # Save using default database
        return user

    # Creates and saves a superuser
    def create_superuser(
        self, email, first_name="", last_name=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)

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


# ======================================================================================
# Organization (Multi-Tenant Backbone)
# For multi tenancy - Each org is identified by domain; used to group users, plans, trials
# ======================================================================================
class Organization(models.Model):
    name = models.CharField(
        max_length=255, unique=True
    )  # Enforced uniqueness to prevent duplicates

    created_at = models.DateTimeField(auto_now_add=True)
    is_personal = models.BooleanField(default=False)  #  True for individuals

    domain = models.CharField(
        max_length=100, blank=True, null=True
    )  # Optional: derived from email

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ======================================================================================
# CUSTOM USER
# User configurations
# ======================================================================================
class CustomUser(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(unique=True, max_length=255)  # Username field

    # Identity fields
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    # Profile metadata
    job_title = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Email verification flag (controlled by token/email flow)
    is_verified_email = models.BooleanField(default=False)

    # Access control
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)  # Used for admin panel
    date_joined = models.DateTimeField(auto_now_add=True)

    @property
    def is_owner(self):
        try:
            return self.membership.role == "owner"
        except Membership.DoesNotExist:
            return False

    @property
    def organization(self):
        try:
            return self.membership.organization
        except Membership.DoesNotExist:
            return None

    USERNAME_FIELD = "email"  # Email is used to log in instead of username
    REQUIRED_FIELDS = [
        "last_name",
    ]

    objects = CustomUserManager()  # Tell Django to use our custom manager

    # Displayed as identifier in admin
    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    @property
    def is_staff(self):
        return self.is_admin


# ==============================================================
# MEMBERSHIP MODEL (User ↔ Org)
# Allows linking users to orgs, with role-based flags like is_owner
# ==============================================================
from django.conf import settings


class Membership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")

    def __str__(self):
        return f"{self.user.email} - {self.role} of {self.organization.name}"


# ======================================================================================
# LICENSE MODEL (Plan Management)
# ======================================================================================
class License(models.Model):
    PLAN_CHOICES = [
        ("standard", "Standard"),
        ("teams", "Teams"),
        ("enterprise", "Enterprise"),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="standard")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_trial = models.BooleanField(default=True)

    def is_active(self):
        return self.end_date >= timezone.now()

    def __str__(self):
        return f"{self.organization.name} – {self.plan.capitalize()}"


class Invite(models.Model):
    email = models.EmailField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    @property
    def is_valid(self):
        return (
            not self.is_expired
            and self.accepted_at is None
            and timezone.now() <= self.created_at + timedelta(days=7)
        )
