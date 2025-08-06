# common/templatetags/common_tags.py

from django import template

register = template.Library()


# ==============================================
# 🔖 TRUST BADGE CSS CLASS FILTER
# ==============================================
@register.filter
def trust_badge_class(score):
    """Returns badge color class based on trust score. | Usage in template: "<span class="{{ score|trust_badge_class }}">{{ score }}</span>" ."""
    try:
        score = int(score)
    except (ValueError, TypeError):
        return "badge bg-secondary text-white"  # fallback

    if score >= 800:
        return "badge bg-success text-white"
    elif score >= 500:
        return "badge bg-warning text-dark"
    else:
        return "badge bg-danger text-white"
