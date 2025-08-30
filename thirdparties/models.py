# Path: thirdparties/models.py

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# =========================
# Choice Enums (TPRM domain)
# =========================
class ThirdPartyLifecycleStatus(models.TextChoices):
    """Business/lifecycle posture (not workflow)."""

    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLACKLISTED = "blacklisted", "Blacklisted"


class ImpactCriticality(models.TextChoices):
    """Business impact if the third party fails."""

    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class RiskTier(models.IntegerChoices):
    """Assurance depth routing (1 = most critical)."""

    TIER_1 = 1, "Tier 1 – Critical"
    TIER_2 = 2, "Tier 2 – Important"
    TIER_3 = 3, "Tier 3 – Standard"


class ServiceModel(models.TextChoices):
    """Service delivery model."""

    SAAS = "saas", "SaaS"
    PAAS = "paas", "PaaS"
    IAAS = "iaas", "IaaS"
    MSP = "msp", "Managed Service"
    CONSULTING = "consulting", "Consulting"
    OTHER = "other", "Other"


class DataSensitivity(models.TextChoices):
    """Highest data sensitivity handled."""

    PUBLIC = "public", "Public"
    INTERNAL = "internal", "Internal"
    CONFIDENTIAL = "confidential", "Confidential"
    RESTRICTED = "restricted", "Restricted"


class EvidenceType(models.TextChoices):
    """Security/compliance evidence categories (URL today; FileField later)."""

    SOC2 = "soc2", "SOC 2"
    ISO27001 = "iso27001", "ISO 27001"
    PEN_TEST = "pentest", "Penetration Test"
    SIG = "sig", "SIG Questionnaire"
    CAIQ = "caiq", "CAIQ"
    DPA = "dpa", "Data Processing Agreement"
    CONTRACT = "contract", "Contract"
    DPIA = "dpia", "DPIA"
    OTHER = "other", "Other"


# =================
# ThirdParty (org-scoped)
# =================
class ThirdParty(models.Model):
    """
    A supplier/service provider (scoped to the tenant Organization).
    Keep this minimal: identity, routing, and a light risk snapshot.
    Deeper scoring and workflows live in other apps.
    """

    # ---- Multi-tenant scoping ------------------------------------------------
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="third_parties",
        help_text="Owning/tenant organization. Enforces per-tenant isolation.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_third_parties",
        help_text="User who first registered this third party.",
    )

    # ---- Identity ------------------------------------------------------------
    name = models.CharField(max_length=255, help_text="Legal or trading name.")
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    # ---- Business posture (not workflow) ------------------------------------
    lifecycle_status = models.CharField(
        max_length=20,
        choices=ThirdPartyLifecycleStatus.choices,
        default=ThirdPartyLifecycleStatus.ACTIVE,
        help_text="Internal business posture. Independent of workflow states.",
    )
    tier = models.IntegerField(
        choices=RiskTier.choices,
        default=RiskTier.TIER_3,
        help_text="Tiering used to pick assessment depth.",
    )
    criticality = models.CharField(
        max_length=10,
        choices=ImpactCriticality.choices,
        default=ImpactCriticality.MEDIUM,
        help_text="Business impact if the third party fails.",
    )

    # ---- Lightweight risk snapshot ------------------------------------------
    risk_snapshot = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0–100 quick snapshot only. Source-of-truth risk lives in assessments.",
    )
    last_assessed = models.DateField(null=True, blank=True)
    next_review_due = models.DateField(null=True, blank=True)

    # ---- Common TPRM flags ---------------------------------------------------
    dpia_required = models.BooleanField(
        default=False,
        help_text="Set when personal data processing requires a DPIA under your policy.",
    )
    processes_pii = models.BooleanField(default=True)
    processes_pci = models.BooleanField(default=False)
    processes_phi = models.BooleanField(default=False)

    # ---- Primary contact channels -------------------------------------------
    support_email = models.EmailField(blank=True)
    security_contact_email = models.EmailField(blank=True)
    security_portal_url = models.URLField(blank=True)

    # ---- Soft delete & timestamps -------------------------------------------
    archived = models.BooleanField(
        default=False,
        help_text="Soft-delete flag used by archive actions and list filters.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---- Optional workflow integration hooks --------------------------------
    tenant_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="For SAME_TENANT workflow guards if you use a workflow engine.",
    )
    wf_state = models.CharField(
        max_length=50,
        default="DRAFT",
        help_text="External workflow state mirror (DRAFT/REVIEW/SUBMITTED/COMPLETE...).",
    )

    class Meta:
        verbose_name = "Third Party"
        verbose_name_plural = "Third Parties"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["wf_state"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["criticality"]),
            models.Index(fields=["archived"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_thirdparty_name_per_org",
            )
        ]
        # Permissions align with a 4-state workflow installer (perm-ns: thirdparty)
        permissions = [
            ("can_submit", "Can submit third party for approval"),
            ("can_request_changes", "Can request changes on third party"),
            ("can_reject", "Can reject third party"),
            ("can_complete", "Can mark third party as complete"),
        ]

    def __str__(self) -> str:
        org = getattr(self.organization, "name", "Unknown Org")
        return f"{self.name} ({org})"

    @property
    def is_active(self) -> bool:
        return (
            self.lifecycle_status == ThirdPartyLifecycleStatus.ACTIVE
            and not self.archived
        )


# =================
# ThirdParty Trust Profile
# =================
class ThirdPartyTrustProfile(models.Model):
    """
    One-to-one trust snapshot for a third party.
    Heavy scoring logic executed in services/trust engine; this stores the last result.
    """

    third_party = models.OneToOneField(
        "thirdparties.ThirdParty",
        on_delete=models.CASCADE,
        related_name="trust_profile",
    )
    # VendorGuard Trust Index is 0–1000 in your design; keep it non-null with a safe default.
    trust_score = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="VendorGuard Trust Index (0–1000).",
    )
    notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["trust_score"]),
            models.Index(fields=["archived"]),
        ]

    def __str__(self):
        return f"{self.third_party.name} trust: {self.trust_score}"


# =================
# ThirdParty contacts
# =================
class ThirdPartyContact(models.Model):
    """Named contact at the third party (unique email per third party)."""

    third_party = models.ForeignKey(
        "thirdparties.ThirdParty",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    role = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["third_party__name", "-is_primary", "name"]
        indexes = [models.Index(fields=["third_party", "email"])]
        constraints = [
            models.UniqueConstraint(
                fields=["third_party", "email"],
                name="uniq_contact_email_per_thirdparty",
            )
        ]

    def __str__(self):
        star = "★ " if self.is_primary else ""
        return f"{star}{self.name} <{self.email}> @ {self.third_party.name}"


# =================
# ThirdParty domains
# =================
class ThirdPartyDomain(models.Model):
    """Domains used by the third party (allowlists, mail policy, filters)."""

    third_party = models.ForeignKey(
        "thirdparties.ThirdParty",
        on_delete=models.CASCADE,
        related_name="domains",
    )
    domain = models.CharField(max_length=191)

    class Meta:
        ordering = ["third_party__name", "domain"]
        indexes = [models.Index(fields=["third_party", "domain"])]
        constraints = [
            models.UniqueConstraint(
                fields=["third_party", "domain"],
                name="uniq_domain_per_thirdparty",
            )
        ]

    def __str__(self):
        return f"{self.domain} ({self.third_party.name})"


# =================
# ThirdParty evidence (docs)
# =================
class ThirdPartyEvidence(models.Model):
    """Evidence references for due diligence. URL-only now; FileField later."""

    third_party = models.ForeignKey(
        "thirdparties.ThirdParty",
        on_delete=models.CASCADE,
        related_name="evidence",
    )
    evidence_type = models.CharField(
        max_length=20,
        choices=EvidenceType.choices,
        default=EvidenceType.OTHER,
    )
    title = models.CharField(max_length=255)
    url = models.URLField(blank=True, help_text="Link to externally stored evidence.")
    issued_date = models.DateField(null=True, blank=True)
    expires_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Third Party Evidence"
        verbose_name_plural = "Third Party Evidence"
        ordering = ["third_party__name", "evidence_type", "-issued_date"]
        indexes = [models.Index(fields=["third_party", "evidence_type"])]

    def __str__(self):
        return f"{self.third_party.name} – {self.get_evidence_type_display()}: {self.title}"


# ===============
# ThirdParty services (offerings)
# ===============
class ThirdPartyService(models.Model):
    """A specific product/service a ThirdParty provides."""

    third_party = models.ForeignKey(
        "thirdparties.ThirdParty",
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    service_type = models.CharField(
        "Solution Type",
        max_length=20,
        choices=ServiceModel.choices,
        default=ServiceModel.SAAS,
    )
    data_sensitivity = models.CharField(
        max_length=20,
        choices=DataSensitivity.choices,
        default=DataSensitivity.CONFIDENTIAL,
        help_text="Highest sensitivity handled by this service.",
    )

    processes_pii = models.BooleanField(default=True)
    processes_pci = models.BooleanField(default=False)
    processes_phi = models.BooleanField(default=False)

    archived = models.BooleanField(
        default=False,
        help_text="Soft-delete flag used by archive actions and list filters.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Third Party Solution"
        verbose_name_plural = "Third Party Solutions"
        ordering = ["third_party__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["third_party", "name"],
                name="uniq_service_name_per_thirdparty",
            )
        ]
        indexes = [
            models.Index(fields=["third_party", "name"]),
            models.Index(fields=["service_type"]),
            models.Index(fields=["archived"]),
        ]

    def __str__(self):
        return f"{self.third_party.name} – {self.name}"
