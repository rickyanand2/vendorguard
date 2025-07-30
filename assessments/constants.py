# assessments/constants.py
import os
from datetime import date
from uuid import uuid4

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


# ------------------ Risk & Info Classification ------------------
class RiskLevels:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"
    UNDETERMINED = "undetermined"

    choices = [
        (LOW, _("Low")),
        (MEDIUM, _("Medium")),
        (HIGH, _("High")),
        (SEVERE, _("Severe")),
        (UNDETERMINED, _("Undetermined")),
    ]


class InfoValueChoices(TextChoices):
    LOW = "low", "Low - Public or non-sensitive"
    MODERATE = "moderate", "Moderate - Internal or confidential"
    HIGH = "high", "High - Regulated or sensitive"
    CRITICAL = "critical", "Critical - Highly sensitive or life-impacting"


class InfoValueLevels:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

    choices = [
        (LOW, _("Low")),
        (MODERATE, _("Moderate")),
        (HIGH, _("High")),
        (CRITICAL, _("Critical")),
    ]


# ------------------ Assessment Enums ------------------
class CertificationTypes(TextChoices):
    GDPR = "GDPR", "GDPR"
    ISO_27001 = "ISO_27001", "ISO 27001"
    SOC2 = "SOC2", "SOC 2 Type 2"
    PCI_DSS = "PCI_DSS", "PCI DSS"
    IRAP = "IRAP", "IRAP"


class ResponseTypes(TextChoices):
    CHOICE = "choice", "Choice (Yes/No/etc.)"
    TEXT = "text", "Text Only"
    CHOICE_TEXT = "choice+text", "Choice with Explanation"


class AnswerChoices(TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"
    PARTIAL = "partial", "Partially"
    NA = "n/a", "Not Applicable"


class AssessmentStatuses(TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    REVIEWED = "reviewed", "Reviewed"


class QuestionCategories(TextChoices):
    DATA_PROTECTION = "data_protection", "Data Protection"
    ACCESS_CONTROL = "access_control", "Access Control"
    INCIDENT_RESPONSE = "incident_response", "Incident Response"
    COMPLIANCE = "compliance", "Regulatory Compliance"
    BUSINESS_CONTINUITY = "bc_dr", "Business Continuity & DR"
    THIRD_PARTY = "third_party", "Third-Party Risk"
    CLOUD_SECURITY = "cloud_security", "Cloud Security"
    VULNERABILITY_MGMT = "vuln_mgmt", "Vulnerability Management"


# ------------------ File Upload Utility ------------------
def evidence_upload_path(instance, filename):
    """Save evidence files under: /evidence/<offering_id>/<date>/<uuid>.<ext>
    """
    ext = filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"
    return os.path.join(
        "evidence",
        f"{instance.assessment.vendor_offering.id}",
        str(date.today()),
        filename,
    )
