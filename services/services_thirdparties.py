# Path: services/services_thirdparties.py
"""
Minimal service helpers for Third Parties and their Services/Solutions.

Assumptions:
- Views pass a logged-in user that already has `user.organization`.
- Organization is never taken from user input and never shown in forms.
"""

from __future__ import annotations

import logging
from typing import Optional
from django.db import transaction

logger = logging.getLogger(__name__)

# Optional trust engine; safe default to 0 if absent
try:
    from trust.engine import calculate_thirdparty_trust_score as _TRUST_CALC  # type: ignore
except Exception:
    _TRUST_CALC = None


def _calc_trust(third_party) -> Optional[int]:
    if _TRUST_CALC is None:
        return None
    try:
        return _TRUST_CALC(third_party)
    except Exception:
        logger.exception(
            "Trust engine failed for ThirdParty id=%s", getattr(third_party, "id", None)
        )
        return None


class CrossTenantViolation(PermissionError):
    """Raised when a write attempts to cross organization boundaries."""


def _ensure_same_org(user, obj, field_name: str = "organization"):
    user_org = getattr(user, "organization", None)
    obj_org = getattr(obj, field_name, None)
    if not user_org or not obj_org or user_org.pk != obj_org.pk:
        raise CrossTenantViolation(
            f"Cross-tenant write prevented: user org {getattr(user_org,'pk',None)} "
            f"!= object org {getattr(obj_org,'pk',None)}"
        )


# ─────────────────────────────────────────────
# Third Party + Trust Profile
# ─────────────────────────────────────────────


@transaction.atomic
def create_thirdparty_with_trust(user, thirdparty_form, trust_form):
    """
    Create ThirdParty + TrustProfile in one transaction.
    Org is taken from `user.organization` only.
    """
    org = getattr(user, "organization", None)
    if org is None:
        raise RuntimeError(
            "User has no organization assigned. Attach one to the user before creating third parties."
        )

    tp = thirdparty_form.save(commit=False)
    tp.organization = org
    if hasattr(tp, "created_by"):
        tp.created_by = user
    tp.save()

    trust = trust_form.save(commit=False)
    if not hasattr(trust, "third_party"):
        raise AttributeError(
            "ThirdPartyTrustProfile must have a `third_party` relation."
        )
    trust.third_party = tp

    score = _calc_trust(tp)
    if hasattr(trust, "trust_score"):
        trust.trust_score = 0 if score is None else score
    trust.save()
    return tp


@transaction.atomic
def update_thirdparty_with_trust(third_party, thirdparty_form, trust_form):
    """Update ThirdParty + TrustProfile; keep org unchanged; recompute trust."""
    tp = thirdparty_form.save(commit=False)
    if getattr(tp, "organization_id", None) is None:
        tp.organization_id = getattr(third_party, "organization_id", None)
    tp.save()

    trust = trust_form.save(commit=False)
    if not hasattr(trust, "third_party"):
        raise AttributeError(
            "ThirdPartyTrustProfile must have a `third_party` relation."
        )
    trust.third_party = tp

    score = _calc_trust(tp)
    if hasattr(trust, "trust_score"):
        trust.trust_score = 0 if score is None else score
    trust.save()
    return tp


def archive_thirdparty(third_party):
    """Soft-archive with sensible fallbacks. Idempotent."""
    if hasattr(third_party, "archived"):
        if not getattr(third_party, "archived", False):
            third_party.archived = True
            third_party.save(update_fields=["archived"])
        return
    if hasattr(third_party, "wf_state"):
        if getattr(third_party, "wf_state", None) != "ARCHIVED":
            third_party.wf_state = "ARCHIVED"
            third_party.save(update_fields=["wf_state"])
        return
    if hasattr(third_party, "lifecycle_status"):
        try:
            from thirdparties.models import ThirdPartyLifecycleStatus

            target = ThirdPartyLifecycleStatus.INACTIVE
        except Exception:
            target = "inactive"
        if getattr(third_party, "lifecycle_status", None) != target:
            third_party.lifecycle_status = target
            third_party.save(update_fields=["lifecycle_status"])


# ─────────────────────────────────────────────
# Third Party Service (“Solution”)
# ─────────────────────────────────────────────


def create_thirdparty_service(third_party, user, form):
    """Create a service/solution under a ThirdParty. Enforce tenant isolation."""
    _ensure_same_org(user, third_party)
    svc = form.save(commit=False)
    if not hasattr(svc, "third_party"):
        raise AttributeError("ThirdPartyService must have a `third_party` relation.")
    svc.third_party = third_party
    if hasattr(svc, "created_by"):
        svc.created_by = user
    svc.save()
    return svc


def update_thirdparty_service(service, form):
    """Update an existing service/solution."""
    return form.save()


def archive_thirdparty_service(service):
    """Soft-archive a service/solution; fallback to wf_state if needed."""
    if hasattr(service, "archived"):
        if not getattr(service, "archived", False):
            service.archived = True
            service.save(update_fields=["archived"])
        return
    if hasattr(service, "wf_state"):
        if getattr(service, "wf_state", None) != "ARCHIVED":
            service.wf_state = "ARCHIVED"
            service.save(update_fields=["wf_state"])


# ─────────────────────────────────────────────
# On-demand trust recompute
# ─────────────────────────────────────────────


def update_thirdparty_score(third_party):
    """Recompute and persist trust score on ThirdPartyTrustProfile (creates if missing)."""
    try:
        from thirdparties.models import ThirdPartyTrustProfile
    except Exception:
        logger.exception("Cannot import ThirdPartyTrustProfile.")
        return

    score = _calc_trust(third_party)
    score_to_set = 0 if score is None else score

    trust, created = ThirdPartyTrustProfile.objects.get_or_create(
        third_party=third_party,
        defaults={"trust_score": score_to_set},
    )
    if not created and getattr(trust, "trust_score", None) != score_to_set:
        try:
            trust.save(update_fields=["trust_score", "updated_at"])
        except Exception:
            trust.save(update_fields=["trust_score"])
