# accounts/views.py
"""Function-based views for accounts (HTMX-friendly, no business logic)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect

import common.errors as ERR
import services.services_accounts as svc
from accounts.forms import (
    AcceptInviteForm,
    InviteForm,
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    RegisterSoloForm,
    RegisterTeamOwnerForm,
)
from accounts.models import Membership


# ===== Auth ===================================================================
@csrf_protect
def login_view(request: HttpRequest) -> HttpResponse:
    """Email/password login."""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            password = form.cleaned_data["password"]
            user = authenticate(request, username=email, password=password)
            if user:
                try:
                    svc.auth_guard_login_attempt(
                        user,
                        ip=request.META.get("REMOTE_ADDR"),
                        ua=request.META.get("HTTP_USER_AGENT", ""),
                    )
                except (ERR.LockedOut, ERR.MFARequired, ERR.IPAccessDenied) as e:
                    messages.error(request, str(e))
                    return render(
                        request, "accounts/login.html", {"form": form}, status=403
                    )

                login(request, user)  # session rotation handled by Django
                svc.auth_record_successful_login(
                    user,
                    ip=request.META.get("REMOTE_ADDR"),
                    ua=request.META.get("HTTP_USER_AGENT", ""),
                )
                messages.success(request, "Welcome back!")
                return redirect("accounts:team_manage")
            else:
                # Increment failed counter if the email exists
                from accounts.models import CustomUser

                try:
                    existing = CustomUser.objects.get(email=email)
                    svc.auth_record_failed_login(existing)
                except CustomUser.DoesNotExist:
                    pass
                messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Logout user."""
    logout(request)
    messages.info(request, "Signed out.")
    return redirect("accounts:login")


# ===== Registration ===========================================================
@csrf_protect
def register_solo_view(request: HttpRequest) -> HttpResponse:
    """Register a solo owner (business email enforced)."""
    if request.method == "POST":
        form = RegisterSoloForm(request.POST)
        if form.is_valid():
            try:
                user = svc.registration_guarded_solo(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    job_title=form.cleaned_data.get("job_title"),
                )
                token = svc.email_issue_token(user)  # dev flow shows token
                messages.success(request, f"Verify email with token (dev): {token}")
                return redirect("accounts:login")
            except ERR.InvalidEmailDomain as e:
                messages.error(request, str(e))
    else:
        form = RegisterSoloForm()
    return render(request, "accounts/register_solo.html", {"form": form})


@csrf_protect
def register_team_owner_view(request: HttpRequest) -> HttpResponse:
    """Register team owner and create org."""
    if request.method == "POST":
        form = RegisterTeamOwnerForm(request.POST)
        if form.is_valid():
            try:
                user = svc.registration_guarded_team_owner(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    org_name=form.cleaned_data["org_name"],
                    domain=form.cleaned_data.get("domain"),
                    job_title=form.cleaned_data.get("job_title"),
                )
                token = svc.email_issue_token(user)  # dev flow shows token
                messages.success(request, f"Verify email with token (dev): {token}")
                return redirect("accounts:login")
            except ERR.InvalidEmailDomain as e:
                messages.error(request, str(e))
    else:
        form = RegisterTeamOwnerForm()
    return render(request, "accounts/register_team.html", {"form": form})


# ===== Email Verification & Password Reset ===================================
@csrf_protect
def email_verify_view(request: HttpRequest) -> HttpResponse:
    """Verify email by token (?token=...)."""
    token = request.GET.get("token") or request.POST.get("token")
    if not token:
        return HttpResponseBadRequest("Missing token.")
    try:
        svc.email_verify(token)
        messages.success(request, "Email verified.")
    except ERR.InvalidToken as e:
        messages.error(request, str(e))
    return redirect("accounts:login")


@csrf_protect
def password_reset_request_view(request: HttpRequest) -> HttpResponse:
    """Start password reset (dev-friendly token)."""
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        from accounts.models import CustomUser

        try:
            user = CustomUser.objects.get(email=form.cleaned_data["email"].lower())
            token = svc.password_issue_reset(user)
            messages.success(request, f"Reset token (dev): {token}")
        except CustomUser.DoesNotExist:
            messages.info(
                request, "If the email exists, a reset token has been issued."
            )
        return redirect("accounts:password_reset_request")
    return render(request, "accounts/password_reset_request.html", {"form": form})


@csrf_protect
def password_reset_confirm_view(request: HttpRequest) -> HttpResponse:
    """Confirm password reset by token."""
    form = PasswordResetConfirmForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            svc.password_reset_with_token(
                form.cleaned_data["token"], form.cleaned_data["new_password"]
            )
            messages.success(request, "Password updated. Please sign in.")
            return redirect("accounts:login")
        except ERR.InvalidToken as e:
            messages.error(request, str(e))
    return render(request, "accounts/password_reset_confirm.html", {"form": form})


# ===== Team management (HTMX-friendly) =======================================
@login_required
def team_manage_view(request: HttpRequest) -> HttpResponse:
    """Team management dashboard."""
    q = (request.GET.get("q") or "").strip().lower()
    org = svc.membership_primary_org(request.user)
    memberships = (
        Membership.objects.filter(organization=org, is_active=True)
        .select_related("user")
        .order_by("user__email")
    )
    if q:
        memberships = memberships.filter(user__email__icontains=q)
    return render(
        request, "accounts/team_manage.html", {"memberships": memberships, "query": q}
    )


@login_required
@csrf_protect
def invite_member_view(request: HttpRequest) -> HttpResponse:
    """Invite member (HTMX modal submit)."""
    form = InviteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        org = svc.membership_primary_org(request.user)
        try:
            invite = svc.invite_create(
                form.cleaned_data["email"], org, form.cleaned_data["role"]
            )
            link_url = svc.invite_build_link(invite, request)
            # dev: inline success content for modal body
            return HttpResponse(
                f"<div class='alert alert-success mb-0'>Invite URL (dev): {link_url}</div>"
            )
        except (ERR.InvalidEmailDomain, ERR.AlreadyMember, ERR.DuplicateInvite) as e:
            return HttpResponse(str(e), status=400)
    return render(request, "accounts/modals/_invite_member.html", {"form": form})


@login_required
@csrf_protect
def change_member_role_view(request: HttpRequest, member_id: int) -> HttpResponse:
    """Change member role (inline select)."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required.")
    m = get_object_or_404(Membership, pk=member_id)
    from accounts import choices as CH  # local import to keep global imports lean

    new_role = request.POST.get("role")
    if new_role not in CH.MembershipRole.values:
        return HttpResponseBadRequest("Invalid role.")
    svc.membership_change_role(m, new_role)
    return team_members_partial_view(request)


@login_required
def team_members_partial_view(request: HttpRequest) -> HttpResponse:
    """Render members table partial (HTMX target)."""
    org = svc.membership_primary_org(request.user)
    q = (request.GET.get("q") or "").strip().lower()
    memberships = (
        Membership.objects.filter(organization=org, is_active=True)
        .select_related("user")
        .order_by("user__email")
    )
    if q:
        memberships = memberships.filter(user__email__icontains=q)
    return render(
        request, "accounts/partials/_member_table.html", {"memberships": memberships}
    )


@login_required
@csrf_protect
def remove_member_view(request: HttpRequest, member_id: int) -> HttpResponse:
    """Remove member (HTMX modal confirm)."""
    m = get_object_or_404(Membership, pk=member_id)
    if request.method == "POST":
        try:
            svc.membership_remove_member(request.user, m)
            return team_members_partial_view(request)
        except ERR.LastOwnerRemovalError as e:
            return HttpResponse(str(e), status=400)
    return render(request, "accounts/modals/_remove_member.html", {"membership": m})


# ===== Invite accept (public) =================================================
@csrf_protect
def accept_invite_view(request: HttpRequest) -> HttpResponse:
    """Accept invite by token."""
    if request.method == "POST":
        form = AcceptInviteForm(request.POST)
        if form.is_valid():
            try:
                svc.invite_accept(
                    token=form.cleaned_data["token"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data.get("first_name", ""),
                    last_name=form.cleaned_data.get("last_name", ""),
                )
                messages.success(request, "Invite accepted. You can sign in now.")
                return redirect("accounts:login")
            except (ERR.InvalidInvite, ERR.BusinessRuleError) as e:
                messages.error(request, str(e))
    else:
        form = AcceptInviteForm(initial={"token": request.GET.get("token", "")})
    return render(request, "accounts/accept_invite.html", {"form": form})
