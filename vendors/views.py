# vendors/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from vendors.models import Vendor, VendorTrustProfile, VendorOffering
from vendors.forms import VendorForm, VendorTrustProfileForm, VendorOfferingForm

from services.vendors import calculate_vendor_trust_score


# ============================================================
# ✅ All Vendor CRUD Views
# ============================================================
class VendorViews(LoginRequiredMixin, View):
    # 🔹 Render vendor list scoped to organization
    @staticmethod
    def list(request):
        vendors = (
            Vendor.objects.prefetch_related("offerings")
            .filter(
                organization=request.user.organization,
                archived=False,
            )
            .order_by("-created_at")
        )
        return render(request, "vendors/vendor_list.html", {"vendors": vendors})

    # 🔹 Show create vendor form (GET) or process submission (POST)
    @staticmethod
    def create(request):
        vendor_form = VendorForm(request.POST or None)
        trust_form = VendorTrustProfileForm(request.POST or None)

        if (
            request.method == "POST"
            and vendor_form.is_valid()
            and trust_form.is_valid()
        ):
            vendor = vendor_form.save(commit=False)
            vendor.organization = request.user.organization
            vendor.created_by = request.user
            vendor.save()

            trust = trust_form.save(commit=False)
            trust.vendor = vendor
            trust.trust_score = calculate_vendor_trust_score(vendor=vendor)
            trust.save()

            messages.success(request, "Vendor created successfully.")
            return redirect("vendors:vendor_list")

        return VendorViews._render_forms(request, vendor_form, trust_form)

    # 🔹 Show edit vendor form (GET) or process update (POST)
    @staticmethod
    def update(request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)

        vendor_form = VendorForm(request.POST or None, instance=vendor)
        trust_form = VendorTrustProfileForm(
            request.POST or None, instance=trust_profile
        )

        if (
            request.method == "POST"
            and vendor_form.is_valid()
            and trust_form.is_valid()
        ):
            vendor_form.save()
            trust = trust_form.save(commit=False)
            trust.trust_score = calculate_vendor_trust_score(trust)
            trust.save()

            messages.success(request, "Vendor updated successfully.")
            return redirect("vendors:vendor_list")

        return VendorViews._render_forms(
            request, vendor_form, trust_form, edit_mode=True
        )

    # 🔹 Render vendor detail page
    @staticmethod
    def detail(request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization, archived=False
        )
        offerings = vendor.offerings.filter(archived=False)

        return render(
            request,
            "vendors/vendor_detail.html",
            {
                "vendor": vendor,
                "offerings": offerings,
            },
        )

    # 🔹 Soft-delete (archive) vendor
    @staticmethod
    def archive(request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        vendor.archived = True
        vendor.save()
        messages.success(request, f"Vendor '{vendor.name}' archived.")
        return redirect("vendors:vendor_list")

    # 🔸 Internal DRY method for rendering dual form
    @staticmethod
    def _render_forms(request, vendor_form, trust_form, edit_mode=False):
        return render(
            request,
            "vendors/vendor_form.html",
            {
                "form": vendor_form,
                "trust_form": trust_form,
                "edit_mode": edit_mode,
            },
        )


# ============================================================
# ✅ All Vendor Offering CRUD Views Grouped in One Class
# ============================================================
class VendorOfferingViews(LoginRequiredMixin, View):
    """
    Grouped offering logic:
    - list: All offerings under this user's organization
    - create: Add offering for a specific vendor
    - update: Edit a vendor offering
    - detail: View offering
    - archive: Soft-delete offering
    """

    # 🔹 List all offerings under user's org (optionally grouped)
    @staticmethod
    def list(request):
        offerings = (
            VendorOffering.objects.filter(
                vendor__organization=request.user.organization,
                archived=False,
            )
            .select_related("vendor")
            .order_by("-created_at")
        )
        return render(request, "vendors/offering_list.html", {"offerings": offerings})

    # 🔹 Create an offering for a given vendor
    @staticmethod
    def create(request, vendor_id):
        vendor = get_object_or_404(
            Vendor, pk=vendor_id, organization=request.user.organization
        )
        form = VendorOfferingForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            offering = form.save(commit=False)
            offering.vendor = vendor
            offering.created_by = request.user
            offering.save()
            messages.success(request, f"Offering added to Vendor: {vendor.name}.")
            return redirect("vendors:offering_list")

        return VendorOfferingViews._render_form(request, form, vendor=vendor)

    # 🔹 Edit existing offering
    @staticmethod
    def update(request, pk):
        offering = get_object_or_404(
            VendorOffering,
            pk=pk,
            vendor__organization=request.user.organization,
        )
        form = VendorOfferingForm(request.POST or None, instance=offering)

        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(
                request, f"Offering updated for Vendor: {offering.vendor.name}."
            )
            return redirect("vendors:offering_list")

        return VendorOfferingViews._render_form(
            request, form, vendor=offering.vendor, edit_mode=True
        )

    # 🔹 View details of an offering
    @staticmethod
    def detail(request, pk):
        offering = get_object_or_404(
            VendorOffering,
            pk=pk,
            vendor__organization=request.user.organization,
        )
        return render(request, "vendors/offering_detail.html", {"offering": offering})

    # 🔹 Archive (soft-delete) offering
    @staticmethod
    def archive(request, pk):
        offering = get_object_or_404(
            VendorOffering,
            pk=pk,
            vendor__organization=request.user.organization,
        )
        offering.archived = True
        offering.save()
        messages.success(request, f"Offering '{offering.name}' archived.")
        return redirect("vendors:vendor_detail", pk=offering.vendor.id)

    # 🔸 Internal DRY method for rendering form
    @staticmethod
    def _render_form(request, form, vendor, edit_mode=False):
        return render(
            request,
            "vendors/offering_form.html",
            {
                "form": form,
                "vendor": vendor,
                "edit_mode": edit_mode,
            },
        )
