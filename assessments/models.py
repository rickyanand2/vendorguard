from django.db import models
from vendors.models import Vendor, Solution
from accounts.models import Organization


class Questionnaire(models.Model):
    """
    Represents a reusable questionnaire template.
    Each questionnaire contains a set of security/risk questions
    used across multiple vendor assessments.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    Represents a single question that belongs to a questionnaire.
    Includes optional help text and a weight to indicate importance.
    """

    RESPONSE_TYPES = [
        ("choice", "Choice (Yes/No/etc.)"),
        ("text", "Text Only"),
        ("choice+text", "Choice with Explanation"),
    ]
    response_type = models.CharField(
        max_length=20,
        choices=RESPONSE_TYPES,
        default="choice",
        help_text="Controls how the question is displayed and answered.",
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    text = models.TextField()
    help_text = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField(
        default=1, help_text="Used in risk scoring calculations"
    )

    def __str__(self):
        return self.text


class Assessment(models.Model):
    """
    An instance of a questionnaire being used to assess a specific vendor
    by a specific organization. Tracks status and aggregate score.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("reviewed", "Reviewed"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    solution = models.ForeignKey(
        Solution, on_delete=models.CASCADE, related_name="assessments"
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    score = models.FloatField(
        default=0.0, help_text="Overall score after assessment completion"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.solution.name} Assessment ({self.status})"

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("organization", "solution", "questionnaire")


class Answer(models.Model):
    """
    Stores the answer to a specific question in the context of a specific assessment.
    Supports structured responses and optional comments.
    """

    ANSWER_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
        ("partial", "Partially"),
        ("n/a", "Not Applicable"),
    ]

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.TextField()  # 👈 THIS MUST EXIST
    answer = models.CharField(max_length=10, choices=ANSWER_CHOICES)
    comments = models.TextField(
        blank=True, help_text="Optional justification or context"
    )
    risk_impact = models.FloatField(
        default=0.0, help_text="Custom risk value (0.0–1.0 scale)"
    )

    class Meta:
        unique_together = ("assessment", "question")

    def __str__(self):
        return f"Answer: {self.question.text[:40]} – {self.answer}"
