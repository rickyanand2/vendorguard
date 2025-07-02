# assessments/constants.py

from django.utils.translation import gettext_lazy as _

CERTIFICATION_TYPES = [
    ("GDPR", _("GDPR")),
    ("ISO_27001", _("ISO 27001")),
    ("SOC2", _("SOC 2 Type 2")),
    ("PCI_DSS", _("PCI DSS")),
    ("IRAP", _("IRAP")),
]


QUESTION_CATEGORIES = [
    ("data_protection", "Data Protection"),
    ("access_control", "Access Control"),
    ("incident_response", "Incident Response"),
    ("business_continuity", "Business Continuity"),
    ("compliance", "Compliance & Legal"),
    ("third_party", "Third Party Risk"),
    ("infrastructure", "Infrastructure Security"),
    ("governance", "Governance & Policy"),
    # Add more as needed
]

RESPONSE_TYPES = [
    ("choice", _("Choice (Yes/No/etc.)")),
    ("text", _("Text Only")),
    ("choice+text", _("Choice with Explanation")),
]

ANSWER_CHOICES = [
    ("yes", _("Yes")),
    ("no", _("No")),
    ("partial", _("Partially")),
    ("n/a", _("Not Applicable")),
]

ASSESSMENT_STATUSES = [
    ("draft", _("Draft")),
    ("submitted", _("Submitted")),
    ("reviewed", _("Reviewed")),
]


def evidence_upload_path(instance, filename):
    return f"evidence/{instance.assessment.vendor_offering.id}/{filename}"
