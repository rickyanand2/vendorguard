from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import CustomUser


# ======================================================================================
# 📝 Solo User Registration Form
# For individuals signing up via public form (creates a personal org automatically)
# ======================================================================================
class CustomSoloUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "job_title",
            "phone",
            "state",
            "country",
            "password1",
            "password2",
        )

        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "John"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Doe"}),
            "email": forms.EmailInput(attrs={"placeholder": "john@example.com"}),
        }


# ======================================================================================
# 🏢 Teams/Enterprise Registration Form
# For orgs signing up via special CTA ("For Teams")
# ======================================================================================
class CustomTeamsCreationForm(UserCreationForm):
    org_name = forms.CharField(label="Organization Name", max_length=255)
    domain = forms.CharField(
        label="Company Domain (e.g. acme.com)",
        max_length=100,
        required=True,
        help_text="Used to associate all users from your domain with your team account",
    )

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "job_title",
            "phone",
            "state",
            "country",
            "password1",
            "password2",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Jane"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Smith"}),
            "email": forms.EmailInput(attrs={"placeholder": "jane@acme.com"}),
        }


class TeamInviteForm(forms.Form):
    email = forms.EmailField(label="Email")
    job_title = forms.CharField(label="Job Title", max_length=100)


# ======================================================================================
# Invite Form
# ======================================================================================
class AcceptInviteForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


# ======================================================================================
# 🔧 Admin Edit Form for CustomUser (visible in Django Admin)
# ======================================================================================
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_admin",  # Uses the @property is_staff
            "job_title",
            "phone",
            "address",
            "state",
            "country",
            "is_verified_email",
        )
