# services/vendors.py


def calculate_trust_score(trust_profile):
    score = 100
    if trust_profile.has_data_breach:
        score -= 30
    if not trust_profile.has_cyber_insurance:
        score -= 20
    return max(score, 0)
