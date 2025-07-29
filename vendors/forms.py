# vendors/forms.py

from django import forms
from .models import Vendor, VendorTrustProfile
from assessments.models import VendorOffering
from vendors.constants import DataType


class VendorOfferingForm(forms.ModelForm):
    data_types_handled = forms.MultipleChoiceField(
        choices=DataType.choices,
        widget=forms.CheckboxSelectMultiple,  # ✅ checkboxes
        required=False,
        label="Types of Data Handled",
    )

    class Meta:
        model = VendorOffering
        fields = [
            "name",
            "description",
            "offering_type",
            "data_location",
            "hosting_provider",
            "hosting_type",
            "stores_data",
            "processes_pii",
            "transmits_data",
            "data_types_handled",
        ]
        labels = {
            "name": "Offering Name",
            "description": "Description",
            "offering_type": "Offering Type",
            "data_location": "Data Storage Location",
            "hosting_provider": "Hosting Provider",
            "hosting_type": "Hosting Type",
            "stores_data": "Stores Data?",
            "processes_pii": "Processes PII?",
            "transmits_data": "Transmits Data?",
            "data_types_handled": "Data Types Handled",
        }
        widgets = {
            "offering_type": forms.RadioSelect,  # Render as radio buttons
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "data_location": forms.TextInput(attrs={"class": "form-control"}),
            "hosting_provider": forms.TextInput(attrs={"class": "form-control"}),
            "hosting_type": forms.Select(attrs={"class": "form-select"}),  # Dropdown
            "data_types_handled": forms.TextInput(attrs={"class": "form-control"}),
            "stores_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "processes_pii": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "transmits_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ---------------- Vendor Form ---------------- #
class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ["name", "industry", "contact_email", "website", "description"]
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


# ---------------- Trust Profile Form ---------------- #
class VendorTrustProfileForm(forms.ModelForm):
    class Meta:
        model = VendorTrustProfile
        fields = [
            "has_cyber_insurance",
            "has_data_breach",
            "last_breach_date",
            "notes",
        ]
        labels = {
            "has_cyber_insurance": "Cyber Liability Insurance",
            "has_data_breach": "Have any data breaches occurred?",
            "last_breach_date": "Date of Last Data Breach",
            "notes": "Additional Security Notes",
        }
        widgets = {
            "last_breach_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }
