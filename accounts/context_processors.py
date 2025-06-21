from .models import Membership


def user_membership(request):
    if not request.user.is_authenticated:
        return {}

    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.user
        )
        return {
            "user_membership": membership,
            "user_organization": membership.organization,
            "is_org_owner": membership.role == "owner",  # ✅ Use this check
        }
    except Membership.DoesNotExist:
        return {}
