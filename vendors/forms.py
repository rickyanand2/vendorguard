# vendors/forms.py
"""Forms for the vendors app (ModelForms only for existing models)."""

from django import forms

from .models import Vendor, VendorOffering


class VendorForm(forms.ModelForm):
    """Create/update a vendor."""

    class Meta:
        model = Vendor
        fields = [
            "organization",
            "name",
            "website",
            "description",
            "status",
            "tier",
            "criticality",
            "risk_rating",
            "last_assessed",
            "next_review_due",
            "dpia_required",
            "processes_pii",
            "processes_pci",
            "processes_phi",
            "support_email",
            "security_contact_email",
            "security_portal_url",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class VendorOfferingForm(forms.ModelForm):
    """Create/update a vendor offering."""

    class Meta:
        model = VendorOffering
        fields = [
            "vendor",
            "name",
            "description",
            "service_type",
            "data_classification",
            "processes_pii",
            "processes_pci",
            "processes_phi",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
