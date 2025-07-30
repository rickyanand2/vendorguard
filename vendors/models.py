# vendors/models.py

from django.conf import settings
from django.db import models

from accounts.models import Organization
from common.models import DataType, TimeStampedModel
from vendors.enums import HostingType, OfferingType


class Vendor(TimeStampedModel):
    """Represents a third-party vendor (company), tied to an Organization.
    """

    # From Accounts Model we get organization | related_name: specifies reverse relationship in Accounts model for this vendor model
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="vendors"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    contact_email = models.EmailField()

    # Archive flag for soft delete
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class VendorOffering(TimeStampedModel):
    """Represents a specific offering/product/service from a Vendor.
    Includes static metadata and current hosting/data profile.
    """

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="offerings"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Offering/ Solution of vendor
    offering_type = models.CharField(
        max_length=50, choices=OfferingType.choices, default=OfferingType.PRODUCT
    )

    # Hosting & Data
    data_location = models.CharField(max_length=255, blank=True)
    hosting_provider = models.CharField(max_length=255, blank=True)
    hosting_type = models.CharField(
        max_length=50, choices=HostingType.choices, blank=True
    )
    stores_data = models.BooleanField(default=False)
    processes_pii = models.BooleanField(default=False)
    transmits_data = models.BooleanField(default=False)

    # From commons - PII, PHI etc.
    data_types_handled = models.ManyToManyField(DataType, blank=True)

    # Cached risk score
    latest_risk_score = models.IntegerField(default=0)

    # Status
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"


class VendorTrustProfile(models.Model):
    """Stores vendor-wide trust posture and breach/insurance status.
    """

    vendor = models.OneToOneField(
        Vendor, on_delete=models.CASCADE, related_name="trust_profile"
    )

    has_cyber_insurance = models.BooleanField(default=False)
    has_data_breach = models.BooleanField(default=False)
    last_breach_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    trust_score = models.IntegerField(
        default=0, help_text="Score calculated based on trust signals (0–100)"
    )

    def __str__(self):
        return f"{self.vendor.name} Trust Profile"
