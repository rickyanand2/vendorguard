# vendors/model.py
from django.db import models
from django.conf import settings
from accounts.models import Organization
from vendors.constants import OfferingType
import os
from uuid import uuid4
from common.models import TimeStampedModel


# Handles per-tenant + per-vendor upload structure for certification artifacts
def cert_artifact_path(instance, filename):
    # You can customize this path structure
    ext = filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"
    return os.path.join("certifications", str(instance.vendor.id), filename)


class Vendor(TimeStampedModel):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)


class VendorTrustProfile(models.Model):
    """
    Stores vendor-wide trust attributes and calculates an overall trust_score (0–100).
    """

    vendor = models.OneToOneField(
        Vendor, on_delete=models.CASCADE, related_name="trust_profile"
    )

    has_cyber_insurance = models.BooleanField(default=False)
    has_data_breach = models.BooleanField(default=False)
    last_breach_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    trust_score = models.IntegerField(
        default=0, help_text="0–100 score based on trust attributes"
    )

    def __str__(self):
        return f"{self.vendor.name} Trust Profile"


# Offering by a vendor.
class VendorOffering(TimeStampedModel):

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="offerings"
    )
    archived = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    offering_type = models.CharField(
        max_length=50, choices=OfferingType.choices, default=OfferingType.PRODUCT
    )
    risk_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"
