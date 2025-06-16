from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models

########################################################################################
# class CustomUserManager
# Custom user manager handles user and superuser creation || Overrides default user model
########################################################################################


class CustomUserManager(BaseUserManager):

    ##################################################
    # def create_user:
    # Creates and saves a User and checks email is not empty
    ##################################################

    def create_user(
        self, email, full_name, date_of_birth, password=None, **extra_fields
    ):

        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        full_name = extra_fields.pop("full_name", "")

        # Create user object with provided fields
        user = self.model(
            email=email,
            full_name=full_name,
            date_of_birth=date_of_birth,
            **extra_fields
        )

        user.set_password(password)  # Hashes the password securely
        user.save(using=self._db)  # Save using default database
        return user

    ##################################################
    # def create_superuser:
    # Same logic as regular user plus setting extra permissions
    ##################################################
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


########################################################################################
# class CustomUser
# Actual user model
########################################################################################


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)  # Username field
    date_of_birth = models.DateField(null=True, blank=True)
    full_name = models.CharField(max_length=255)

    # These fields are required for admin and auth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Determines admin access

    # Tell Django to use our custom manager
    objects = CustomUserManager()

    # Email is used to log in instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]  # Required for createsuperuser

    def get_full_name(self):
        return self.full_name or ""

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else ""

    def __str__(self):
        return self.email  # Displayed as identifier in admin
