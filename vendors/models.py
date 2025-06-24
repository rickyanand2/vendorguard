from django.db import models
from django.conf import settings
from accounts.models import Organization


class Vendor(models.Model):
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

    def __str__(self):
        return self.name


# Handles per-tenant + per-vendor upload structure for certification artifacts
def cert_artifact_path(instance, filename):
    org = instance.vendor.organization
    return f"cert_artifacts/{org.id}/{instance.vendor.id}/{filename}"


class Certification(models.Model):
    CERT_TYPES = [
        ("GDPR", "GDPR"),
        ("ISO_27001", "ISO 27001"),
        ("SOC2", "SOC 2 Type 2"),
        ("PCI_DSS", "PCI DSS"),
        ("IRAP", "IRAP"),
        # Add more as needed
    ]

    vendor = models.ForeignKey(
        "Vendor", on_delete=models.CASCADE, related_name="certifications"
    )
    type = models.CharField(max_length=50, choices=CERT_TYPES)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    cert_number = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    artifact = models.FileField(
        upload_to=cert_artifact_path,
        null=True,
        blank=True,
        help_text="Optional: Upload certification file",
    )
    external_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.vendor.name} - {self.get_type_display()}"


class VendorTrustProfile(models.Model):
    """
    Stores vendor-wide trust attributes and calculates an overall trust_score (0–100).
    """

    vendor = models.OneToOneField(
        "Vendor", on_delete=models.CASCADE, related_name="trust_profile"
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

    def calculate_trust_score(self):
        score = 0
        """
        Simple additive scoring:
        +25 for GDPR
        +25 for ISO 27001
        +20 for SOC 2
        +20 for cyber insurance
        -20 if breach occurred in last 12 months
        Max: 100
        """
        cert_weights = {
            "GDPR": 25,
            "ISO_27001": 25,
            "SOC2": 20,
            "PCI_DSS": 15,
            "IRAP": 15,
        }

        for cert in self.vendor.certifications.all():
            score += cert_weights.get(cert.type, 0)

        if self.has_cyber_insurance:
            score += 20

        if self.last_breach_date:
            from datetime import date, timedelta

            if self.last_breach_date >= date.today() - timedelta(days=365):
                score -= 20  # Penalize recent breach

        self.trust_score = max(0, min(score, 100))  # Clamp between 0–100
        return self.trust_score  # Avoid saving here directly

    @property
    def aggregate_risk_score(self):
        """
        Returns average risk score of all solution assessments.
        """
        scores = [
            s.assessment.score
            for s in self.vendor.solutions.all()
            if hasattr(s, "assessment") and s.assessment.score is not None
        ]
        return round(sum(scores) / len(scores), 2) if scores else None


# ✅ Solution: Represents a product or service offered by a vendor.
class Solution(models.Model):

    # Each solution can have one assessment.
    SOLUTION_TYPE_CHOICES = [
        ("product", "Product"),
        ("service", "Service"),
        ("integration", "Integration"),
    ]

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="solutions"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    solution_type = models.CharField(
        max_length=50, choices=SOLUTION_TYPE_CHOICES, default="product"
    )

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"
