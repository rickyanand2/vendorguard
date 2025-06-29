# accounts/views.py
import logging
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils.crypto import get_random_string
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.forms import AcceptInviteForm
from django.views.generic import TemplateView

from accounts.forms import (
    CustomSoloUserCreationForm,
    CustomTeamsCreationForm,
    TeamInviteForm,
)
from accounts.models import CustomUser, Membership, License, Invite
from services.accounts import RegistrationService
from services.accounts import InviteService
from services.permissions import OwnerRequiredMixin
from services.memberships import get_org_members
from accounts.forms import TeamInviteForm


logger = logging.getLogger(__name__)  # Setup logging for error tracking


# ====================================================================
# 🔐 Solo User Registration (default public entry point)
# ====================================================================
class SoloRegisterView(FormView):
    form_class = CustomSoloUserCreationForm
    template_name = "accounts/register_solo.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        try:
            user = RegistrationService.register_solo_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                job_title=form.cleaned_data.get("job_title"),
            )
            login(self.request, user)
            messages.success(self.request, "Welcome! Your 14-day trial has started.")
            return super().form_valid(form)

        except ValidationError as ve:
            form.add_error(None, str(ve))
            return self.form_invalid(form)

        except Exception as e:
            logger.exception("Solo registration failed")
            form.add_error(None, f"Unexpected error: {str(e)}")
            return self.form_invalid(form)


# ====================================================================


# ====================================================================
# 🏢 Team/Enterprise Registration (via hidden CTA)
# ====================================================================
class TeamRegisterView(FormView):
    form_class = CustomTeamsCreationForm
    template_name = "accounts/register_team.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        try:
            user = RegistrationService.register_team_owner(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                org_name=form.cleaned_data["org_name"],
                domain=form.cleaned_data["domain"].lower(),
                job_title=form.cleaned_data.get("job_title"),
            )
            login(self.request, user)
            messages.success(
                self.request, f"Team '{form.cleaned_data['org_name']}' created!"
            )
            return super().form_valid(form)
        except ValidationError as ve:
            form.add_error(None, str(ve))
            return self.form_invalid(form)
        except Exception as e:
            logger.exception("Team registration failed")
            form.add_error(None, f"Unexpected error: {str(e)}")
            return self.form_invalid(form)


# ====================================================================


# ====================================================================
# 🔓🔐 User Login and Logout Views
# ====================================================================
class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse("accounts:profile")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("website:home")


# ====================================================================


# ====================================================================
# 👤 Profile View
# ====================================================================
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        membership = getattr(self.request.user, "membership", None)

        if membership is None:
            context["organization"] = None
            context["license"] = None
            context["role"] = None
        else:
            context["organization"] = membership.organization
            context["license"] = License.objects.filter(
                organization=membership.organization
            ).first()
            context["role"] = membership.role

        return context


# ====================================================================


# ====================================================================
# 🧑‍💼 Manage Team (only for Org Owners)
# ====================================================================


class ManageTeamView(OwnerRequiredMixin, FormView):
    template_name = "accounts/team_manage.html"
    form_class = TeamInviteForm
    success_url = reverse_lazy("accounts:manage_team")

    def get_context_data(self, **kwargs):
        # Adds current organization members to the context.
        context = super().get_context_data(**kwargs)
        org = self.membership.organization
        members = get_org_members(self.request.user)
        context.update(
            {
                "members": members,
                "org_domain": org.domain,
            }
        )
        return context

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        job_title = form.cleaned_data["job_title"]
        org = self.membership.organization

        try:
            invite = InviteService.send_invite(
                email=email, job_title=job_title, org=org, request=self.request
            )
            messages.success(self.request, f"Invite sent to {email}.")
            return super().form_valid(form)
        except ValidationError as ve:
            form.add_error(None, str(ve))
            return self.form_invalid(form)
        except Exception as e:
            logger.exception("Error during invite")
            form.add_error(None, f"Unexpected error: {str(e)}")
            return self.form_invalid(form)


# ====================================================================


# ====================================================================
# Invite Users to Org
# ====================================================================
class AcceptInviteView(FormView):
    template_name = "accounts/accept_invite.html"
    form_class = AcceptInviteForm
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        self.token = request.GET.get("token")
        try:
            self.invite = Invite.objects.get(token=self.token)
            if not self.invite.is_valid:
                raise ValueError("Invalid or expired.")
        except Exception:
            messages.error(request, "This invite link is invalid or expired.")
            return redirect("website:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            user = InviteService.accept_invite(
                token=self.token,
                password=form.cleaned_data["password1"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )
            login(self.request, user)
            messages.success(
                self.request, f"Welcome to {self.invite.organization.name}!"
            )
            return super().form_valid(form)
        except Exception as e:
            logger.exception("[AcceptInvite] Error during invite acceptance")
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invite"] = self.invite
        return context


@method_decorator(require_POST, name="dispatch")
class RemoveTeamMemberView(TemplateView):
    def post(self, request, *args, **kwargs):
        logger.info("Team member removal requested (placeholder)")
        return HttpResponse("Removed", status=200)


# ====================================================================
