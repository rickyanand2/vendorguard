# vendors/forms.py
"""Forms for the vendors app (ModelForms only for existing models)."""

from django import forms

from .models import Vendor, VendorOffering


class VendorForm(forms.ModelForm):
    """Create/update a vendor."""

    class Meta:
        model = Vendor
        fields = "__all__"  # 👈 stop hard-coding 'status' (which may not exist yet)
        widgets = {
            # optional: these are ignored if the field doesn't exist in the model
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            # "status": forms.Select(attrs={"class": "form-select"}),  # ignored if absent
        }


class VendorOfferingForm(forms.ModelForm):
    """Create/update a vendor offering."""

    class Meta:
        model = VendorOffering
        fields = "__all__"  # 👈 same idea here
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
