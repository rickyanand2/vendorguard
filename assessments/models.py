# assessments/models.py

from django.db import models
from vendors.models import Vendor, VendorOffering, cert_artifact_path
from accounts.models import Organization
from common.models import TimeStampedModel
from .constants import (
    CERTIFICATION_TYPES,
    RESPONSE_TYPES,
    ANSWER_CHOICES,
    ASSESSMENT_STATUSES,
    QUESTION_CATEGORIES,
    evidence_upload_path,
)


class Certification(TimeStampedModel):

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="certifications"
    )
    type = models.CharField(max_length=50, choices=CERTIFICATION_TYPES)
    is_valid = models.BooleanField(default=False)
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


class Questionnaire(TimeStampedModel):
    """
    Represents a reusable questionnaire template.
    Each questionnaire contains a set of security/risk questions
    used across multiple vendor assessments.
    """

    name = models.CharField(max_length=255)
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    Represents a single question that belongs to a questionnaire.
    Includes optional help text and a weight to indicate importance.
    """

    category = models.CharField(
        max_length=50,
        choices=QUESTION_CATEGORIES,
        default="data_protection",
        help_text="Security domain or category this question belongs to.",
    )

    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    text = models.TextField()
    help_text = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField(
        default=1, help_text="Used in risk scoring calculations"
    )

    def __str__(self):
        return self.text


class Assessment(TimeStampedModel):
    """
    An instance of a questionnaire being used to assess a specific vendor
    by a specific organization. Tracks status and aggregate score.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    vendor_offering = models.ForeignKey(
        VendorOffering, on_delete=models.CASCADE, related_name="assessments"
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20, choices=ASSESSMENT_STATUSES, default="draft"
    )
    score = models.FloatField(
        default=0.0, help_text="Overall score after assessment completion"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor_offering.name} Assessment ({self.status})"

    class Meta:
        ordering = ["-created_at"]


class Answer(TimeStampedModel):
    """
    Stores the answer to a specific question in the context of a specific assessment.
    Supports structured responses and optional comments.
    """

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.TextField()  # 👈 THIS MUST EXIST
    answer = models.CharField(max_length=10, choices=ANSWER_CHOICES)
    comments = models.TextField(
        blank=True, help_text="Optional justification or context"
    )
    evidence = models.FileField(upload_to=evidence_upload_path, null=True, blank=True)
    risk_impact = models.FloatField(
        default=0.0, help_text="Custom risk value (0.0–1.0 scale)"
    )

    class Meta:
        unique_together = ("assessment", "question")

    def __str__(self):
        return f"{self.assessment.id} - {self.question.text[:30]}: {self.answer}"
