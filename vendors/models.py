"""Vendor & offering models (string refs to avoid circular imports)."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# =========================
# Choices (vendor-specific)
# =========================
class VendorStatus(models.TextChoices):
    """Lifecycle state of a vendor."""

    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLACKLISTED = "blacklisted", "Blacklisted"


class Criticality(models.TextChoices):
    """Business impact if vendor fails."""

    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class Tier(models.IntegerChoices):
    """Risk tiering (1=most critical)."""

    TIER_1 = 1, "Tier 1 – Critical"
    TIER_2 = 2, "Tier 2 – Important"
    TIER_3 = 3, "Tier 3 – Standard"


class ServiceType(models.TextChoices):
    """Type of service."""

    SAAS = "saas", "SaaS"
    PAAS = "paas", "PaaS"
    IAAS = "iaas", "IaaS"
    MSP = "msp", "Managed Service"
    CONSULTING = "consulting", "Consulting"
    OTHER = "other", "Other"


class DataClassification(models.TextChoices):
    """Highest data classification processed/stored."""

    PUBLIC = "public", "Public"
    INTERNAL = "internal", "Internal"
    CONFIDENTIAL = "confidential", "Confidential"
    RESTRICTED = "restricted", "Restricted"


class DocumentType(models.TextChoices):
    """Security/compliance document categories (URL-based for now)."""

    SOC2 = "soc2", "SOC 2"
    ISO27001 = "iso27001", "ISO 27001"
    PEN_TEST = "pentest", "Penetration Test"
    SIG = "sig", "SIG Questionnaire"
    CAIQ = "caiq", "CAIQ"
    DPA = "dpa", "Data Processing Agreement"
    CONTRACT = "contract", "Contract"
    DPIA = "dpia", "DPIA"
    OTHER = "other", "Other"


# ===========
# Vendor
# ===========
class Vendor(models.Model):
    """Third-party company (scoped to an Organization)."""

    organization = models.ForeignKey(
        "accounts.Organization",  # string ref prevents circular imports
        on_delete=models.CASCADE,
        related_name="vendors",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_vendors",
    )

    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=VendorStatus.choices,
        default=VendorStatus.ACTIVE,
    )
    tier = models.IntegerField(
        choices=Tier.choices,
        default=Tier.TIER_3,
    )
    criticality = models.CharField(
        max_length=10,
        choices=Criticality.choices,
        default=Criticality.MEDIUM,
    )

    # Simple risk snapshot (keep it flexible; detailed scoring can live in assessments app)
    risk_rating = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0–100 snapshot score.",
    )
    last_assessed = models.DateField(null=True, blank=True)
    next_review_due = models.DateField(null=True, blank=True)

    # Flags often needed in TPRM
    dpia_required = models.BooleanField(default=False)
    processes_pii = models.BooleanField(default=True)
    processes_pci = models.BooleanField(default=False)
    processes_phi = models.BooleanField(default=False)

    # Basic contact channel (primary). Detailed contacts live in VendorContact.
    support_email = models.EmailField(blank=True)
    security_contact_email = models.EmailField(blank=True)
    security_portal_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["criticality"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_vendor_name_per_org",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"


# =================
# Vendor contacts
# =================
class VendorContact(models.Model):
    """Named contact at a vendor (per org's view of that vendor)."""

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    role = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["vendor__name", "-is_primary", "name"]
        indexes = [models.Index(fields=["vendor", "email"])]
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "email"],
                name="uniq_contact_email_per_vendor",
            )
        ]

    def __str__(self) -> str:
        star = "★ " if self.is_primary else ""
        return f"{star}{self.name} <{self.email}> @ {self.vendor.name}"


# =================
# Vendor domains
# =================
class VendorDomain(models.Model):
    """Domains used by the vendor (allowlists, email policy, filters)."""

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="domains",
    )
    domain = models.CharField(max_length=191)

    class Meta:
        ordering = ["vendor__name", "domain"]
        indexes = [models.Index(fields=["vendor", "domain"])]
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "domain"],
                name="uniq_domain_per_vendor",
            )
        ]

    def __str__(self) -> str:
        return f"{self.domain} ({self.vendor.name})"


# =================
# Vendor documents
# =================
class VendorDocument(models.Model):
    """Security/compliance document references (URL for now)."""

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    title = models.CharField(max_length=255)
    url = models.URLField(blank=True, help_text="Link to externally stored evidence.")
    # If you later add MEDIA storage, switch to:
    # file = models.FileField(upload_to="vendor_docs/", blank=True)

    issued_date = models.DateField(null=True, blank=True)
    expires_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["vendor__name", "doc_type", "-issued_date"]
        indexes = [models.Index(fields=["vendor", "doc_type"])]

    def __str__(self) -> str:
        return f"{self.vendor.name} – {self.get_doc_type_display()}: {self.title}"


# ===============
# Vendor offering
# ===============
class VendorOffering(models.Model):
    """A specific product/service offered by a Vendor."""

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="offerings",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.SAAS,
    )
    data_classification = models.CharField(
        max_length=20,
        choices=DataClassification.choices,
        default=DataClassification.CONFIDENTIAL,
        help_text="Highest classification handled by this offering.",
    )

    processes_pii = models.BooleanField(default=True)
    processes_pci = models.BooleanField(default=False)
    processes_phi = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vendor__name", "name"]
        unique_together = ("vendor", "name")
        indexes = [
            models.Index(fields=["vendor", "name"]),
            models.Index(fields=["service_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.vendor.name} – {self.name}"
