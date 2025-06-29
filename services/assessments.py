# services/assessments.py
from django.shortcuts import get_object_or_404
from assessments.models import Assessment, Answer, Questionnaire, Question
from accounts.models import Membership
from workflow.utils import perform_transition
from vendors.models import VendorTrustProfile, VendorOffering


# =========================
# Custom Exceptions
# =========================
class NoQuestionnaireError(Exception):
    pass


class AssessmentAlreadyExists(Exception):
    def __init__(self, existing_assessment):
        self.existing_assessment = existing_assessment


# =========================


# =========================
# Start a new assessment
# =========================
def start_assessment_for_solution(user, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)
    org = user.membership.organization

    if hasattr(solution, "assessment"):
        return solution.assessment  # Already exists

    questionnaire = Questionnaire.objects.order_by("id").first()
    if not questionnaire:
        raise NoQuestionnaireError("No questionnaire available.")

    existing = Assessment.objects.filter(
        organization=org,
        solution=solution,
        questionnaire=questionnaire,
    ).first()

    if existing:
        print(">>> Returning existing assessment", existing.id)
        raise AssessmentAlreadyExists(existing)

    return Assessment.objects.create(
        solution=solution,
        organization=org,
        questionnaire=questionnaire,
    )


# =========================


# =========================
# Submit answers to assessment
# =========================
def submit_answers(user, assessment_id, post_data):
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        organization=user.membership.organization,
    )

    questions = Question.objects.filter(questionnaire=assessment.questionnaire)

    for question in questions:
        response = post_data.get(f"response_{question.id}")
        if response:
            Answer.objects.update_or_create(
                assessment=assessment,
                question=question,
                defaults={"response": response},
            )

    # Scoring
    total_weight = 0
    score = 0
    for question in questions:
        try:
            answer = Answer.objects.get(assessment=assessment, question=question)
            weight = question.weight or 1
            total_weight += weight
            if answer.response.lower() == "yes":
                score += weight
        except Answer.DoesNotExist:
            continue

    assessment.status = "submitted"
    assessment.score = (score / total_weight) * 100 if total_weight else 0
    assessment.save()
    return assessment


# =========================


# =========================
# Perform workflow transition
# =========================
def transition_assessment_to_review(user, assessment_id):
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        organization=user.membership.organization,
    )

    success, message = perform_transition(
        obj=assessment,
        to_state_name="Review",
        user=user,
        comment="Submitted for review",
    )

    return success, message, assessment


# =========================

"""
    Calculates average risk score from all assessments linked to the vendor's offerings.
    Returns None if no assessments exist or if all scores are missing.
"""


def calculate_aggregate_vendor_risk_score(vendor):
    offerings = VendorOffering.objects.filter(vendor=vendor)
    trust_score = (
        vendor.trust_profile.trust_score if hasattr(vendor, "trust_profile") else 0
    )

    offering_scores = sum(o.risk_score or 0 for o in offerings)

    return offering_scores + trust_score


"""
    Recalculates and saves the trust_score on the vendor's trust profile.

    Args:
        vendor: Vendor instance
        create_if_missing: whether to create the VendorTrustProfile if it doesn't exist
"""


def update_vendor_trust_score(vendor, create_if_missing=True):

    score = calculate_aggregate_vendor_risk_score(vendor)

    trust_profile = getattr(vendor, "trust_profile", None)
    if not trust_profile and create_if_missing:
        trust_profile = VendorTrustProfile.objects.create(vendor=vendor)

    if trust_profile:
        trust_profile.trust_score = score or 0
        trust_profile.save()

    return score


# services/trust_profile.py
from datetime import date, timedelta


# ==================================================
# Trust Profile Scoring Logic
# Returns a trust score (0–100) based on vendor certifications and profile data.
# ==================================================
class VendorTrustProfileService:
    def __init__(self, vendor):
        self.vendor = vendor
        self.profile = vendor.trust_profile

    def get_cert_weights(self):
        """
        Simple additive scoring:
        +25 for GDPR
        +25 for ISO 27001
        +20 for SOC 2
        +20 for cyber insurance
        -20 if breach occurred in last 12 months
        Max: 100
        """
        return {
            "GDPR": 25,
            "ISO_27001": 25,
            "SOC2": 20,
            "PCI_DSS": 15,
            "IRAP": 15,
        }

    def calculate_score(self):
        score = 0
        cert_weights = self.get_cert_weights()

        for cert in self.vendor.certifications.all():
            score += cert_weights.get(cert.type, 0)

        if self.profile.has_cyber_insurance:
            score += 20

        if self.profile.last_breach_date:
            from datetime import date, timedelta

            if self.profile.last_breach_date >= date.today() - timedelta(days=365):
                score -= 20

        return max(0, min(score, 100))

    def update_score(self):
        self.profile.trust_score = self.calculate_score()
        self.profile.save()
        return self.profile.trust_score
