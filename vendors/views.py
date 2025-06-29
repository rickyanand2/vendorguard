# vendors/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from vendors.models import Vendor, VendorTrustProfile
from vendors.forms import VendorForm, VendorTrustProfileForm
from services.assessments import calculate_aggregate_vendor_risk_score
from services.vendors import calculate_trust_score


# ============================================================
# ✅ ListView for Vendors (scoped to user's organization)
# ============================================================
class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = "vendors/vendor_list.html"
    context_object_name = "vendors"

    def get_queryset(self):
        return Vendor.objects.filter(
            organization=self.request.user.organization, archived=False
        ).order_by("-created_at")


# ============================================================
# ✅ Add Vendor + Trust Profile (manual CBV for dual-form)
# ============================================================
class VendorCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return self.render_forms(VendorForm(), VendorTrustProfileForm())

    def post(self, request):
        vendor_form = VendorForm(request.POST)
        trust_form = VendorTrustProfileForm(request.POST)

        if vendor_form.is_valid() and trust_form.is_valid():
            vendor = vendor_form.save(commit=False)
            vendor.organization = request.user.organization
            vendor.created_by = request.user
            vendor.save()

            trust = trust_form.save(commit=False)
            trust.vendor = vendor
            trust.trust_score = calculate_aggregate_vendor_risk_score(vendor=vendor)
            trust.save()

            return redirect("vendors:vendor_list")

        return self.render_forms(vendor_form, trust_form)

    def render_forms(self, vendor_form, trust_form):
        return render(
            self.request,
            "vendors/vendor_form.html",
            {
                "form": vendor_form,
                "trust_form": trust_form,
            },
        )


# ============================================================
# ✅ Edit Vendor + Trust Profile
# ============================================================
class VendorUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)
        return self.render_forms(
            VendorForm(instance=vendor),
            VendorTrustProfileForm(instance=trust_profile),
        )

    def post(self, request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)

        vendor_form = VendorForm(request.POST, instance=vendor)
        trust_form = VendorTrustProfileForm(request.POST, instance=trust_profile)

        if vendor_form.is_valid() and trust_form.is_valid():
            vendor_form.save()
            trust = trust_form.save(commit=False)
            trust.trust_score = calculate_trust_score(trust)
            trust.save()
            return redirect("vendors:vendor_list")

        return self.render_forms(vendor_form, trust_form)

    def render_forms(self, vendor_form, trust_form):
        return render(
            self.request,
            "vendors/vendor_form.html",
            {
                "form": vendor_form,
                "trust_form": trust_form,
                "edit_mode": True,
            },
        )


# ============================================================
# ✅ Soft-delete Vendor (Archive)
# ============================================================
class VendorArchiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        vendor.archived = True
        vendor.save()
        messages.success(request, f"Vendor '{vendor.name}' archived.")
        return redirect("vendors:vendor_list")
