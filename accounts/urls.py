# accounts/urls.py
from django.urls import path

from accounts.views import (
    AcceptInviteView,
    ManageTeamView,
    ProfileView,
    UserLoginView,
    UserLogoutView,
)

from . import views
from .views import SoloRegisterView, TeamRegisterView

app_name = "accounts"  # 👈 Important for namespacing

urlpatterns = [
    path("register/", SoloRegisterView.as_view(), name="register_solo"),
    path("register/team/", TeamRegisterView.as_view(), name="register_team"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("manage-team/", ManageTeamView.as_view(), name="manage_team"),
    # Invite and remove team members in Team/ Enterprise plans
    path(
        "team/remove/<int:user_id>/",
        views.RemoveTeamMemberView.as_view(),
        name="remove_team_member",
    ),
    path("accept-invite/", AcceptInviteView.as_view(), name="accept_invite"),
]
