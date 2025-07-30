# accounts/tests/test_accounts.py

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Membership, Organization

User = get_user_model()


class BaseAccountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="TestOrg", domain="test.com")
        cls.owner = User.objects.create_user(
            email="owner@test.com",
            first_name="Owner",
            last_name="User",
            password="Password123!",
        )
        cls.user = User.objects.create_user(
            email="member@test.com",
            first_name="Member",
            last_name="User",
            password="Password123!",
        )
        Membership.objects.create(user=cls.owner, organization=cls.org, role="owner")
        Membership.objects.create(user=cls.user, organization=cls.org, role="member")


class RegistrationTests(BaseAccountTestCase):
    def test_register_team_duplicate_domain(self):
        response = self.client.post(
            reverse("accounts:register_team"),
            {
                "org_name": "TestOrg",
                "email": "newuser@test.com",
                "password1": "Password123!",
                "password2": "Password123!",
            },
        )

        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertEqual(response.status_code, 200)


class LoginTests(BaseAccountTestCase):
    def test_login_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.owner.email,
                "password": "Password123!",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_login_fail(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": "member@test.com",
                "password": "WrongPassword",
            },
        )
        self.assertEqual(response.status_code, 200)


class LogoutTests(BaseAccountTestCase):
    def test_logout_view(self):
        self.client.login(username="member@test.com", password="Password123!")

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("website:home"))


class ProfileViewTests(BaseAccountTestCase):
    def test_profile_access_authenticated(self):
        self.client.login(email="owner@test.com", password="Password123!")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner User")

    def test_redirects_if_not_logged_in(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)


class TeamManagementTests(BaseAccountTestCase):
    def test_remove_team_member_htmx(self):
        self.client.login(email="owner@test.com", password="Password123!")
        response = self.client.post(
            reverse("accounts:remove_team_member", args=[self.user.id]),
            {"user_id": self.user.id},
            HTTP_HX_REQUEST="true",
        )
        self.assertIn(response.status_code, [200, 302])
