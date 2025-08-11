"""Template context helpers."""

from accounts.models import Membership


def user_membership(request):
    """Expose the current user's primary membership/org to templates."""
    org = None
    try:
        if request.user.is_authenticated:
            m = (
                Membership.objects.filter(
                    user=request.user, is_active=True, is_primary=True
                )
                .select_related("organization")
                .first()
            )
            if m:
                org = m.organization
    except Exception:
        org = None
    return {"current_org": org}
