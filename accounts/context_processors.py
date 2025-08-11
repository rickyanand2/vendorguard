# accounts/context_processors.py
"""Template context helpers for the accounts app."""

from __future__ import annotations

from django.http import HttpRequest

from accounts.models import Membership


def user_membership(request: HttpRequest) -> dict:
    """Expose the user's primary org and membership to templates."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "current_org": None,
            "current_membership": None,
        }

    # Cache on the request to avoid repeat queries per render.
    if not hasattr(request, "_current_membership"):
        request._current_membership = (
            Membership.objects.select_related("organization")
            .filter(user=user, is_active=True, is_primary=True)
            .first()
            or Membership.objects.select_related("organization")
            .filter(user=user, is_active=True)
            .order_by("organization__name")
            .first()
        )

    m = request._current_membership
    return {
        "current_org": m.organization if m else None,
        "current_membership": m,
    }
