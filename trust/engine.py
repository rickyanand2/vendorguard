# trust/engine.py


def calculate_vendor_trust_score(vendor):
    """Assigns a trust score to vendor"""

    offerings = vendor.offerings.filter(archived=False)
    scores = []

    for offering in offerings:
        if (
            hasattr(offering, "assessment")
            and offering.assessment
            and offering.assessment.calculated_score
        ):
            scores.append(
                offering.assessment.calculated_score
            )  # Or however you compute it

    if not scores:
        return None  # No score if nothing to assess

    return sum(scores) // len(scores)  # Avg trust score or weighted


# ───────────────────────────────────────────
# 🔒 Scoring Component Functions (Each Returns Int)
# ───────────────────────────────────────────


def _security_score(vendor):
    trust = getattr(vendor, "trust_profile", None)
    if not trust:
        return 0
    return 150 if trust.has_cyber_insurance else 0


def _assessment_score(vendor):
    """Calculates assessment completion score for a vendor
    by aggregating over all their offerings' assessments.
    """
    offerings = vendor.offerings.all()
    if not offerings.exists():
        return 0

    completed, total = 0, 0
    for offering in offerings:
        assessments = offering.assessments.all()
        completed += assessments.filter(status="completed").count()
        total += assessments.count()

    return int(200 * (completed / total)) if total else 0


def _certification_score(vendor):
    # Placeholder — you can later inspect attached certifications
    return 100


def _breach_history_score(vendor):
    trust = getattr(vendor, "trust_profile", None)
    if not trust:
        return 0
    return -100 if trust.has_data_breach else 100


def _transparency_score(vendor):
    # Placeholder for whether vendor has filled all required data
    return 100 if vendor.description and vendor.website else 50
