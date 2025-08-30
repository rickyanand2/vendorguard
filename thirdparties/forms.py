# Path: thirdparties/forms.py
"""
Forms for Third Parties and their Services (aka “Solutions”).
Organization is never shown; views/services assign it from request.user.organization.
"""

from django import forms
from .models import ThirdParty, ThirdPartyService, ThirdPartyTrustProfile


class ThirdPartyForm(forms.ModelForm):
    class Meta:
        model = ThirdParty
        fields = [
            "name",
            "website",
            "description",
            "lifecycle_status",
            "tier",
            "criticality",
            "risk_snapshot",
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
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ThirdPartyServiceForm(forms.ModelForm):
    class Meta:
        model = ThirdPartyService
        fields = [
            "name",
            "description",
            "service_type",  # “Solution type” in UI if preferred
            "data_sensitivity",
            "processes_pii",
            "processes_pci",
            "processes_phi",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ThirdPartyTrustProfileForm(forms.ModelForm):
    class Meta:
        model = ThirdPartyTrustProfile
        fields = ["trust_score", "notes"]
