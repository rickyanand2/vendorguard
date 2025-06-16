from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True)
    date_of_birth = forms.DateField(
        required=True, widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = CustomUser
        fields = ("email", "full_name", "date_of_birth", "password1", "password2")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email", "date_of_birth", "is_active", "is_staff")
