# services/vendors.py

from vendors.models import Vendor, VendorTrustProfile
from assessments.models import Assessment, Certification
from datetime import timedelta
from django.utils import timezone


# ============ PILLAR 1: SECURITY READINESS (250 pts) ============
def score_security_readiness(profile: VendorTrustProfile) -> int:
    score = 0

    if not profile.has_data_breach:
        score += 100
    if profile.has_cyber_insurance:
        score += 75
    if profile.privacy_policy_url:
        score += 25
    if profile.security_policy_url:
        score += 25
    if profile.incident_response_url:
        score += 25

    return min(score, 250)


# ============ PILLAR 2: ASSESSMENT INTEGRITY (250 pts) ============
def score_assessment_integrity(vendor: Vendor) -> int:
    total_score = 0.0
    total_count = 0

    for offering in vendor.offerings.filter(archived=False):
        assessments = Assessment.objects.filter(vendor_offering=offering)
        for a in assessments:
            total_score += a.score  # out of 100
            total_count += 1

    if total_count == 0:
        return 0

    avg = total_score / total_count  # still 0–100
    return round((avg / 100.0) * 250)  # Normalize to 250 pts


# ============ PILLAR 3: CERTIFICATION MATURITY (150 pts) ============
def score_certification_maturity(vendor: Vendor) -> int:
    certs = Certification.objects.filter(vendor=vendor)
    score = 0
    now = timezone.now()

    for cert in certs:
        if cert.type in ["SOC2", "ISO27001", "HIPAA"]:
            score += 40
        elif cert.type in ["GDPR", "NIST", "PCI-DSS"]:
            score += 30
        else:
            score += 20

        # Recency bonus
        if cert.valid_until and cert.valid_until > now:
            delta = cert.valid_until - now
            if delta.days > 180:
                score += 10

    return min(score, 150)


# ============ PILLAR 4: HISTORICAL BEHAVIOR (150 pts) ============
def score_behavioral_history(profile: VendorTrustProfile) -> int:
    score = 0
    now = timezone.now()

    if not profile.has_data_breach:
        score += 75
    else:
        # Penalize recent breaches
        if profile.breach_date:
            days_since_breach = (now - profile.breach_date).days
            if days_since_breach > 365:
                score += 25
            elif days_since_breach > 180:
                score += 10

    if profile.last_updated and (now - profile.last_updated).days < 90:
        score += 25  # recently maintained
    if profile.last_updated and (now - profile.last_updated).days < 30:
        score += 25  # very recent

    return min(score, 150)


# ============ PILLAR 5: TRANSPARENCY SIGNALS (200 pts) ============
def score_transparency_signals(profile: VendorTrustProfile) -> int:
    score = 0
    if profile.supporting_documents.exists():
        score += 100
    if profile.attestation_signed:
        score += 50
    if profile.comments or profile.extra_notes:
        score += 25
    if profile.created_by and profile.created_by.is_verified:
        score += 25

    return min(score, 200)


# ============ FINAL CALCULATION ============


def calculate_vendor_trust_score(vendor: Vendor) -> int:
    try:
        profile = vendor.trust_profile
    except VendorTrustProfile.DoesNotExist:
        return 0  # No data means max risk

    total = 0
    total += score_security_readiness(profile)
    total += score_assessment_integrity(vendor)
    total += score_certification_maturity(vendor)
    total += score_behavioral_history(profile)
    total += score_transparency_signals(profile)

    return min(round(total), 1000)


def classify_risk_level(score: int) -> str:
    """
    Categorize vendor trust score into risk levels.
    """
    if score >= 850:
        return "Low"
    elif score >= 650:
        return "Moderate"
    elif score >= 400:
        return "High"
    return "Critical"
