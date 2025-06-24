from django import forms
from .models import Vendor, VendorTrustProfile
from assessments.models import Solution


class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ["name", "description", "solution_type"]
        widgets = {
            "solution_type": forms.RadioSelect,  # 👈 This makes it a radio button
        }


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ["name", "contact_email", "website", "description"]
        labels = {
            "name": "Vendor Name",
            "industry": "Industry",
            "contact_email": "Contact Email",
            "website": "Vendor Website",
            "description": "Description",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VendorTrustProfileForm(forms.ModelForm):
    class Meta:
        model = VendorTrustProfile
        labels = {
            "has_cyber_insurance": "Cyber Liability Insurance",
            "has_data_breach": "Have any data breaches occurred?",
            "last_breach_date": "Date of Last Data Breach",
            "notes": "Additional Security Notes",
        }
        fields = [
            "has_cyber_insurance",
            "has_data_breach",
            "last_breach_date",
            "notes",
        ]

        widgets = {
            "last_breach_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }
