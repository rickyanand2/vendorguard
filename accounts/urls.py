# accounts/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = "accounts"  # 👈 Important for namespacing

urlpatterns = [
    path("register/", views.register_solo, name="register_solo"),
    path("register-team/", views.register_team, name="register_team"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.logout_view, name="logout"),  # ✅ Use your custom logout view
    path("profile/", views.profile, name="profile"),
    path("manage-team/", views.manage_team, name="manage_team"),
    path(
        "remove-member/<int:user_id>/",
        views.remove_team_member,
        name="remove_team_member",
    ),
    # path("invite/", views.invite_user, name="invite_user"),
]
