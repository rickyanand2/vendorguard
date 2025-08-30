# accounts/urls.py
"""URL routes for accounts FBVs."""

from django.urls import path

from accounts import views as v

app_name = "accounts"

urlpatterns = [
    # Auth
    path("login/", v.login_view, name="login"),
    path("logout/", v.logout_view, name="logout"),
    path("profile/", v.profile_view, name="profile"),
    # Registration
    path("register/solo/", v.register_solo_view, name="register_solo"),
    path("register/team/", v.register_team_owner_view, name="register_team"),
    # Email verification + password reset
    path("email/verify/", v.email_verify_view, name="email_verify"),
    path(
        "password/reset-request/",
        v.password_reset_request_view,
        name="password_reset_request",
    ),
    path(
        "password/reset-confirm/",
        v.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
    # Team management (HTMX-friendly)
    path("team/manage/", v.team_manage_view, name="team_manage"),
    path(
        "team/member/<int:user_id>/remove/",
        v.remove_team_member,
        name="remove_team_member",
    ),
    path(
        "team/members/partial/",
        v.team_members_partial_view,
        name="team_members_partial",
    ),
    path("team/invite/", v.invite_member_view, name="invite_member"),
    path(
        "team/member/<int:member_id>/role/",
        v.change_member_role_view,
        name="change_member_role",
    ),
    path(
        "team/member/<int:member_id>/remove/",
        v.remove_member_view,
        name="remove_member",
    ),
    # Public invite accept
    path("invite/accept/", v.accept_invite_view, name="accept_invite"),
]
