from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Organization, Membership

User = get_user_model()


class UserAuthTests(TestCase):

    def test_register_valid_user(self):
        print("\nRunning test_register_valid_user")
        response = self.client.post(
            reverse("accounts:register_solo"),
            {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            },
        )
        print(f"Status Code: {response.status_code}")
        self.assertEqual(
            response.status_code, 302, msg="Registration should redirect on success."
        )
        self.assertTrue(
            User.objects.filter(email="test@example.com").exists(),
            msg="User should be created.",
        )

    def test_register_missing_fields(self):
        print("\nRunning test_register_missing_fields")
        response = self.client.post(
            reverse("accounts:register_solo"),
            {
                "email": "",
                "password1": "pass1234",
                "password2": "pass1234",
            },
        )
        print(f"Status Code: {response.status_code}")
        self.assertEqual(
            response.status_code, 200, msg="Form with missing fields should return 200."
        )
        self.assertIn(
            b"This field is required",
            response.content,
            msg="Should show required field error.",
        )

    def test_login_success(self):
        print("\nRunning test_login_success")
        user = User.objects.create_user(
            email="loginuser@example.com",
            first_name="Login",
            last_name="User",
            password="LoginPass123!",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "loginuser@example.com", "password": "LoginPass123!"},
        )
        print(f"Redirect URL: {response.url}")
        self.assertRedirects(
            response,
            "/dashboard/",
            msg_prefix="User should be redirected to dashboard after login.",
        )

    def test_profile_view_requires_login(self):
        print("\nRunning test_profile_view_requires_login")
        response = self.client.get(reverse("accounts:profile"))
        expected_redirect = (
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}"
        )
        print(f"Redirect URL: {response.url}")
        self.assertRedirects(
            response,
            expected_redirect,
            msg_prefix="Unauthenticated user should be redirected to login.",
        )

    def test_authenticated_user_can_access_profile(self):
        print("\nRunning test_authenticated_user_can_access_profile")
        user = User.objects.create_user(
            email="profile@example.com",
            first_name="Profile",
            last_name="User",
            password="ProfilePass123!",
        )
        self.client.login(username="profile@example.com", password="ProfilePass123!")
        response = self.client.get(reverse("accounts:profile"))
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print("Response content:")
            print(response.content.decode())
        self.assertEqual(
            response.status_code,
            200,
            msg="Authenticated user should access profile page.",
        )
        self.assertIn(
            b"Profile", response.content, msg="Profile page should contain 'Profile'"
        )

    def test_logout_functionality(self):
        print("\nRunning test_logout_functionality")
        user = User.objects.create_user(
            email="logout@example.com",
            first_name="Logout",
            last_name="User",
            password="LogoutPass123!",
        )
        self.client.login(username="logout@example.com", password="LogoutPass123!")
        response = self.client.post(reverse("accounts:logout"))
        print(f"Redirect URL: {response.url}")
        self.assertRedirects(
            response,
            reverse("website:home"),
            msg_prefix="Logout should redirect to home.",
        )

    def test_register_team_duplicate_domain(self):
        print("\nRunning test_register_team_duplicate_domain")
        Organization.objects.create(name="Org1", domain="test.com")
        response = self.client.post(
            reverse("accounts:register_team"),
            {
                "org_name": "TestOrg2",
                "domain": "test.com",
                "email": "admin@test.com",
                "password1": "AdminPass123!",
                "password2": "AdminPass123!",
                "first_name": "Admin",
                "last_name": "User",
            },
        )
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"This domain is already in use",
            response.content,
            msg="Should show duplicate domain error.",
        )

    def test_expired_license_logic(self):
        print("\nRunning test_expired_license_logic")
        # Placeholder test — update when License model is implemented
        pass

    def test_team_member_invite_htmx(self):
        print("\nRunning test_team_member_invite_htmx")
        owner = User.objects.create_user(
            email="owner@test.com",
            first_name="Owner",
            last_name="User",
            password="pass1234",
        )
        org = Organization.objects.create(name="TestOrg", domain="owner.com")
        Membership.objects.create(user=owner, organization=org, role="owner")
        self.client.login(username="owner@test.com", password="pass1234")
        response = self.client.get(
            reverse("accounts:manage_team"), HTTP_HX_REQUEST="true"
        )
        print(f"Status Code: {response.status_code}")
        self.assertEqual(
            response.status_code, 200, msg="HTMX invite team view should return 200."
        )

    def test_team_member_remove_htmx(self):
        print("\nRunning test_team_member_remove_htmx")
        owner = User.objects.create_user(
            email="owner2@test.com",
            first_name="Owner2",
            last_name="User",
            password="pass1234",
        )
        member = User.objects.create_user(
            email="member@test.com",
            first_name="Member",
            last_name="User",
            password="pass1234",
        )
        org = Organization.objects.create(name="TestOrg2", domain="owner2.com")
        Membership.objects.create(user=owner, organization=org, role="owner")
        Membership.objects.create(user=member, organization=org, role="member")
        self.client.login(username="owner2@test.com", password="pass1234")
        response = self.client.post(
            reverse("accounts:remove_team_member", kwargs={"user_id": member.id}),
            HTTP_HX_REQUEST="true",
        )
        print(f"Status Code: {response.status_code}")
        self.assertIn(
            response.status_code,
            [200, 302],
            msg="HTMX remove team member should return 200 or 302.",
        )
