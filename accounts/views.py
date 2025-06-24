from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import Http404, HttpResponse, HttpResponseForbidden
from datetime import timedelta
import logging

from .forms import CustomSoloUserCreationForm, CustomTeamsCreationForm, TeamInviteForm
from .models import CustomUser, Organization, Membership, License


logger = logging.getLogger(__name__)  # Setup logging for error tracking

# 🚫 Block public email domains for enterprise accounts
BLOCKED_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
}


# Utility to extract domain from email
def extract_email_domain(email):
    return email.split("@")[1].lower()


# -------------------------------------------------------
# 🔐 Solo User Registration (default public entry point)
# -------------------------------------------------------
def register_solo(request):
    if request.method == "POST":
        form = CustomSoloUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # 1. Shared solo org for all individual users
                org, _ = Organization.objects.get_or_create(
                    name="VendorGuard Solo",
                    domain="solo.vendor",
                    is_personal=True,
                )

                # 2. Trial license setup (14-day default)
                License.objects.get_or_create(
                    organization=org,
                    defaults={
                        "plan": "standard",
                        "is_trial": True,
                        "start_date": timezone.now().date(),
                        "end_date": timezone.now().date() + timedelta(days=14),
                    },
                )

                # 3. Save user and assign membership
                user = form.save()
                Membership.objects.create(user=user, organization=org, role="owner")

                # 4. Log in and redirect
                login(request, user)
                messages.success(request, "Welcome! Your 14-day trial has started.")
                return redirect("accounts:profile")

            except Exception as e:
                logger.exception("Solo registration failed")
                form.add_error(None, f"An unexpected error occurred: {str(e)}")
    else:
        form = CustomSoloUserCreationForm()

    return render(request, "accounts/register_solo.html", {"form": form})


# -------------------------------------------------------
# 🏢 Team/Enterprise Registration (via hidden CTA)
# -------------------------------------------------------
def register_team(request):
    if request.method == "POST":
        form = CustomTeamsCreationForm(request.POST)
        if form.is_valid():
            try:
                org_name = form.cleaned_data["org_name"]
                domain = form.cleaned_data["domain"].lower()
                email_domain = extract_email_domain(form.cleaned_data["email"])

                # Block known public domains
                if domain in BLOCKED_DOMAINS or email_domain in BLOCKED_DOMAINS:
                    form.add_error("email", "Public email providers are not allowed.")
                    return render(
                        request, "accounts/register_team.html", {"form": form}
                    )

                # Prevent duplicate orgs by domain
                if Organization.objects.filter(domain=domain).exists():
                    form.add_error("domain", "This domain is already in use.")
                    return render(
                        request, "accounts/register_team.html", {"form": form}
                    )

                # Create org and license
                org = Organization.objects.create(
                    name=org_name, domain=domain, is_personal=False
                )
                License.objects.create(
                    organization=org,
                    plan="teams",
                    is_trial=True,
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timedelta(days=14),
                )

                # Register user as org owner
                user = form.save(commit=False)
                user.save()

                # ✅ Make this user the owner
                Membership.objects.create(user=user, organization=org, role="owner")

                login(request, user)
                messages.success(request, f"Team '{org_name}' created successfully!")
                return redirect("accounts:profile")

            except Exception as e:
                logger.exception("Team registration failed")
                form.add_error(None, f"Unexpected error during registration: {str(e)}")
    else:
        form = CustomTeamsCreationForm()

    return render(request, "accounts/register_team.html", {"form": form})


# --------------------------
# 🔐 Login View
# --------------------------
def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard:dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


# --------------------------
# 🔓 Logout View
# --------------------------
def logout_view(request):
    logout(request)
    return redirect("website:home")


# --------------------------
# 👤 Profile View
# --------------------------
@login_required
def profile(request):
    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.user
        )
    except Membership.DoesNotExist:
        raise Http404("Membership not found. Please contact support.")

    license = License.objects.filter(organization=membership.organization).first()

    context = {
        "user": request.user,
        "org": membership.organization,
        "license": license,
        "is_owner": membership.role == "owner",
    }
    return render(request, "accounts/profile.html", context)


# -------------------------------------------------------
# 🧑‍💼 Manage Team (only for Org Owners)
# -------------------------------------------------------
@login_required
def manage_team(request):
    membership = Membership.objects.filter(user=request.user).first()
    if not membership or membership.role != "owner":
        return HttpResponseForbidden("You do not have permission to access this page.")

    org = membership.organization
    members = Membership.objects.filter(organization=org).select_related("user")

    if request.method == "POST":
        form = TeamInviteForm(request.POST)
        if form.is_valid():
            try:
                invite_email = form.cleaned_data["email"]
                job_title = form.cleaned_data["job_title"]

                new_user = CustomUser.objects.create_user(
                    email=invite_email,
                    password=CustomUser.objects.make_random_password(),
                    job_title=job_title,
                )
                Membership.objects.create(
                    user=new_user, organization=org, role="member"
                )
                messages.success(request, f"{invite_email} has been invited.")

                return redirect("accounts:manage_team")

            except Exception as e:
                logger.exception("Error inviting user")
                messages.error(request, f"Failed to invite: {str(e)}")

    else:
        form = TeamInviteForm()

    return render(
        request, "accounts/team_manage.html", {"form": form, "members": members}
    )


# Placeholder / Functionality to be implementeds
@login_required
def invite_user_placeholder(request):
    return render(
        request,
        "accounts/feature_placeholder.html",
        {
            "feature_name": "Invite Team Member",
        },
    )


# --------------------------
# ❌ Remove Member (AJAX/HTMX) - Placeholder / Functionality to be implemented
# --------------------------
@login_required
def remove_team_member_placeholder(request, user_id):
    """
    membership = Membership.objects.filter(user=request.user).first()
    if not membership or membership.role != "owner":
        return HttpResponseForbidden("Only owners can remove members.")

    user_to_remove = get_object_or_404(CustomUser, id=user_id)
    target_membership = Membership.objects.filter(
        user=user_to_remove, organization=membership.organization
    ).first()

    if target_membership:
        user_to_remove.delete()
        return HttpResponse("")  # HTMX partial update
    return HttpResponseForbidden("Unauthorized.")
    """
    return render(
        request,
        "accounts/feature_placeholder.html",
        {
            "feature_name": f"Remove Team Member (User ID: {user_id})",
        },
    )
