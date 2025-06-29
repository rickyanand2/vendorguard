# services/memberships.py
from django.contrib.auth.models import AnonymousUser  # To handle non logged in users
from accounts.models import Membership, CustomUser


# 🔍 Get the current user's membership (e.g., to check org, role, etc.)
def get_user_membership(user: CustomUser) -> Membership | None:
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return None
    return Membership.objects.select_related("organization").filter(user=user).first()


# 👥 Get all members in the user's organization
def get_org_members(user: CustomUser) -> list[Membership]:
    membership = get_user_membership(user)
    if not membership:
        return []
    return (
        Membership.objects.select_related("user")
        .filter(organization=membership.organization)
        .order_by("user__first_name")
    )
