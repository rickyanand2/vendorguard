from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Organization, Membership, License

User = get_user_model()


class UserAuthTests(TestCase):
    """
    Test suite for user authentication, registration, team management, and access control.
    """

    def test_register_valid_user(self):
        response = self.client.post(
            reverse("accounts:register_solo"),
            {
                "email": "test@example.com",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_register_missing_fields(self):
        response = self.client.post(
            reverse("accounts:register_solo"),
            {
                "email": "",
                "password1": "pass1234",
                "password2": "pass1234",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")

    def test_login_success(self):
        user = User.objects.create_user(
            email="loginuser@example.com",
            password="LoginPass123!",
            first_name="Login",
            last_name="User",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "loginuser@example.com", "password": "LoginPass123!"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={reverse('profile')}"
        )

    def test_logout_functionality(self):
        user = User.objects.create_user(
            email="logout@example.com",
            password="LogoutPass123!",
            first_name="Logout",
            last_name="User",
        )
        self.client.login(username="logout@example.com", password="LogoutPass123!")
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("home"))

        profile_response = self.client.get(reverse("profile"))
        self.assertRedirects(
            profile_response, f"{reverse('accounts:login')}?next={reverse('profile')}"
        )

    def test_authenticated_user_can_access_profile(self):
        user = User.objects.create_user(
            email="profile@example.com",
            password="Profile123!",
            first_name="Profile",
            last_name="User",
        )
        self.client.login(username="profile@example.com", password="Profile123!")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profile")

    def test_register_team_duplicate_domain(self):
        org = Organization.objects.create(name="TestOrg", domain="test.com")
        response = self.client.post(
            reverse("accounts:register_team"),
            {
                "org_name": "TestOrg2",
                "domain": "test.com",
                "email": "admin@test.com",
                "password1": "TeamPass123!",
                "password2": "TeamPass123!",
                "first_name": "Admin",
                "last_name": "User",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Organization with this domain already exists")

    def test_expired_license_logic(self):
        org = Organization.objects.create(name="ExpiredOrg", domain="expired.com")
        license = License.objects.create(
            organization=org,
            plan="standard",
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        user = User.objects.create_user(
            email="expired@ex.com",
            password="Expired123!",
            first_name="Expired",
            last_name="User",
        )
        Membership.objects.create(user=user, organization=org, role="owner")
        self.client.login(username="expired@ex.com", password="Expired123!")

        response = self.client.get(reverse("profile"))
        self.assertContains(response, "Your license has expired")

    def test_team_member_invite_htmx(self):
        org = Organization.objects.create(name="Org1", domain="org1.com")
        owner = User.objects.create_user(
            email="owner@org1.com",
            password="pass123",
            first_name="Owner",
            last_name="Org",
        )
        Membership.objects.create(user=owner, organization=org, role="owner")
        self.client.login(username="owner@org1.com", password="pass123")

        response = self.client.post(
            reverse("accounts:invite_member"),
            {"email": "newmember@org1.com"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "newmember@org1.com")

    def test_team_member_remove_htmx(self):
        org = Organization.objects.create(name="Org1", domain="org1.com")
        owner = User.objects.create_user(
            email="owner@org1.com",
            password="pass123",
            first_name="Owner",
            last_name="Org",
        )
        member = User.objects.create_user(
            email="member@org1.com",
            password="pass123",
            first_name="Member",
            last_name="User",
        )
        Membership.objects.create(user=owner, organization=org, role="owner")
        Membership.objects.create(user=member, organization=org, role="member")
        self.client.login(username="owner@org1.com", password="pass123")

        response = self.client.post(
            reverse("accounts:remove_member", kwargs={"user_id": member.id}),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(member, org.members.all())
