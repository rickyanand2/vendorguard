# common/forms.py

from django import forms


class TestForm(forms.Form):
    """Test form used for test_layout.html."""

    first_name = forms.CharField(
        label="First Name",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    role = forms.ChoiceField(
        label="Role",
        choices=[("admin", "Admin"), ("member", "Member")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    document = forms.FileField(
        label="Upload Document",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    notes = forms.CharField(
        label="Notes",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        required=False,
    )
    confirm = forms.BooleanField(
        label="I confirm the above details",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
