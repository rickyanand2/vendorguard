# accounts/mixins.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden

from accounts.constants import ROLE_OWNER
from services.memberships import get_user_membership


class OwnerRequiredMixin(LoginRequiredMixin):
    """Requires user to be logged in AND an organization owner.
    Redirects unauthenticated users (via LoginRequiredMixin),
    returns 403 for authenticated but unauthorized users.
    """

    def dispatch(self, request, *args, **kwargs):
        # ✅ Let LoginRequiredMixin handle unauthenticated first
        response = super().dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated:
            return response

        # ✅ Authenticated, now check role
        if not request.user.is_superuser:
            membership = get_user_membership(request.user)
            if not membership or membership.role != ROLE_OWNER:
                return HttpResponseForbidden(
                    "Only organization owners can access this page."
                )

            self.membership = membership

        return response
