# services/permissions.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseForbidden

from accounts.models import Membership

# ---------------------------------------------------------------------
# ✅ Utility Functions
# ---------------------------------------------------------------------


# Get user membership
def get_user_membership(user):
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return None
    return Membership.objects.select_related("organization").filter(user=user).first()


# Get user org
def get_user_org(user):
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return None
    membership = get_user_membership(user)
    return membership.organization if membership else None


# ---------------------------------------------------------------------
# ✅ Mixin to ensure the user belongs to an organization.| Injects `self.organization` for reuse
# ---------------------------------------------------------------------
class OrganizationRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        org = get_user_org(request.user)
        if not org:
            return HttpResponseForbidden("You must belong to an organization.")
        self.organization = org
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------
# ✅ Mixin to ensure the user is an organization owner. | Injects `self.membership` for reuse.
# ---------------------------------------------------------------------
class OwnerRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        membership = get_user_membership(request.user)
        if not membership or membership.role != "owner":
            return HttpResponseForbidden(
                "Only organization owners can access this page."
            )
        self.membership = membership
        return super().dispatch(request, *args, **kwargs)
