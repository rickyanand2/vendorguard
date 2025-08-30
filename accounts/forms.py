# accounts/forms.py
"""Forms for accounts FBVs (validation only; no business logic)."""

from __future__ import annotations

from django import forms

from accounts import choices as CH


class LoginForm(forms.Form):
    """Email/password login."""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class RegisterSoloForm(forms.Form):
    """Solo registration (business email enforced in services)."""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    job_title = forms.CharField(max_length=100, required=False)


class RegisterTeamOwnerForm(forms.Form):
    """Team/owner registration."""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    org_name = forms.CharField(max_length=255)
    domain = forms.CharField(max_length=191, required=False)
    job_title = forms.CharField(max_length=100, required=False)


class InviteForm(forms.Form):
    """Invite a member to org."""

    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=CH.MembershipRole.choices, initial=CH.MembershipRole.MEMBER
    )
    job_title = forms.CharField(max_length=100, required=False)


class PasswordResetRequestForm(forms.Form):
    """Start password reset."""

    email = forms.EmailField()


class PasswordResetConfirmForm(forms.Form):
    """Confirm password reset by token."""

    token = forms.CharField(max_length=64)
    new_password = forms.CharField(widget=forms.PasswordInput)


class AcceptInviteForm(forms.Form):
    """Accept invite and create account."""

    token = forms.CharField(max_length=64)
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
