# vendors/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from vendors.models import Vendor, VendorTrustProfile, VendorOffering
from vendors.forms import VendorForm, VendorTrustProfileForm, VendorOfferingForm

from services.services_vendors import (
    create_vendor_with_trust,
    update_vendor_with_trust,
    archive_vendor,
    create_vendor_offering,
    update_vendor_offering,
    archive_vendor_offering,
)

# For Archive Class
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from vendors.constants import DataType

# ============================================================
# ✅ Vendor Views (List / Create / Update / Detail / Archive)
# ============================================================


class VendorListView(LoginRequiredMixin, ListView):
    """Display all non-archived vendors under the user's organization."""

    model = Vendor
    template_name = "vendors/vendor_list.html"
    context_object_name = "vendors"

    def get_queryset(self):
        return (
            Vendor.objects.prefetch_related("offerings")
            .filter(organization=self.request.user.organization, archived=False)
            .order_by("-created_at")
        )


class VendorDetailView(LoginRequiredMixin, DetailView):
    """Show vendor details and associated offerings."""

    model = Vendor
    template_name = "vendors/vendor_detail.html"
    context_object_name = "vendor"

    def get_queryset(self):
        return Vendor.objects.filter(
            organization=self.request.user.organization, archived=False
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["offerings"] = self.object.offerings.filter(archived=False)
        return context


class VendorCreateView(LoginRequiredMixin, View):
    """Create a new vendor with a trust profile."""

    def get(self, request):
        return self._render_form(request, VendorForm(), VendorTrustProfileForm())

    def post(self, request):
        vendor_form = VendorForm(request.POST)
        trust_form = VendorTrustProfileForm(request.POST)

        if vendor_form.is_valid() and trust_form.is_valid():
            create_vendor_with_trust(request.user, vendor_form, trust_form)
            messages.success(request, "Vendor created successfully.")
            return redirect("vendors:vendor_list")

        return self._render_form(request, vendor_form, trust_form)

    def _render_form(self, request, vendor_form, trust_form, edit_mode=False):
        return render(
            request,
            "vendors/vendor_form.html",
            {
                "form": vendor_form,
                "trust_form": trust_form,
                "edit_mode": edit_mode,
            },
        )


class VendorUpdateView(LoginRequiredMixin, View):
    """Update an existing vendor and trust profile."""

    def get(self, request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)
        return self._render_form(
            request,
            VendorForm(instance=vendor),
            VendorTrustProfileForm(instance=trust_profile),
            edit_mode=True,
        )

    def post(self, request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)

        vendor_form = VendorForm(request.POST, instance=vendor)
        trust_form = VendorTrustProfileForm(request.POST, instance=trust_profile)

        if vendor_form.is_valid() and trust_form.is_valid():
            update_vendor_with_trust(vendor, vendor_form, trust_form)
            messages.success(request, "Vendor updated successfully.")
            return redirect("vendors:vendor_list")

        return self._render_form(request, vendor_form, trust_form, edit_mode=True)

    def _render_form(self, request, vendor_form, trust_form, edit_mode=False):
        return render(
            request,
            "vendors/vendor_form.html",
            {
                "form": vendor_form,
                "trust_form": trust_form,
                "edit_mode": edit_mode,
            },
        )


@method_decorator(csrf_protect, name="dispatch")
class VendorArchiveView(LoginRequiredMixin, View):
    """Soft-delete (archive) a vendor."""

    def post(self, request, pk):
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        archive_vendor(vendor)
        messages.success(request, f"Vendor '{vendor.name}' archived.")
        return redirect("vendors:vendor_list")


# ============================================================
# ✅ Vendor Offering Views (List / Create / Update / Detail / Archive)
# ============================================================


class VendorOfferingListView(LoginRequiredMixin, ListView):
    """Display all active offerings across the org."""

    model = VendorOffering
    template_name = "vendors/offering_list.html"
    context_object_name = "offerings"

    def get_queryset(self):
        return (
            VendorOffering.objects.filter(
                vendor__organization=self.request.user.organization,
                archived=False,
            )
            .select_related("vendor")
            .order_by("-created_at")
        )


class VendorOfferingDetailView(LoginRequiredMixin, DetailView):
    """View single offering detail."""

    model = VendorOffering
    template_name = "vendors/offering_detail.html"
    context_object_name = "offering"

    def get_queryset(self):
        return VendorOffering.objects.filter(
            vendor__organization=self.request.user.organization
        )


class VendorOfferingCreateView(LoginRequiredMixin, View):
    """Create an offering under a specific vendor."""

    def get(self, request, vendor_id):
        vendor = get_object_or_404(
            Vendor, pk=vendor_id, organization=request.user.organization
        )
        return self._render_form(request, VendorOfferingForm(), vendor)

    def post(self, request, vendor_id):
        vendor = get_object_or_404(
            Vendor, pk=vendor_id, organization=request.user.organization
        )
        form = VendorOfferingForm(request.POST)

        if form.is_valid():
            create_vendor_offering(vendor, request.user, form)
            messages.success(request, f"Offering added to Vendor: {vendor.name}.")
            return redirect("vendors:offering_list")

        return self._render_form(request, form, vendor)

    def _render_form(self, request, form, vendor, edit_mode=False):
        return render(
            request,
            "vendors/offering_form.html",
            {
                "form": form,
                "vendor": vendor,
                "edit_mode": edit_mode,
            },
        )


class VendorOfferingUpdateView(LoginRequiredMixin, View):
    """Update an existing vendor offering."""

    def get(self, request, pk):
        offering = get_object_or_404(
            VendorOffering, pk=pk, vendor__organization=request.user.organization
        )
        return self._render_form(
            request, VendorOfferingForm(instance=offering), offering.vendor
        )

    def post(self, request, pk):
        offering = get_object_or_404(
            VendorOffering, pk=pk, vendor__organization=request.user.organization
        )
        form = VendorOfferingForm(request.POST, instance=offering)

        if form.is_valid():
            update_vendor_offering(offering, form)
            messages.success(
                request, f"Offering updated for Vendor: {offering.vendor.name}."
            )
            return redirect("vendors:offering_list")

        return self._render_form(request, form, offering.vendor, edit_mode=True)

    def _render_form(self, request, form, vendor, edit_mode=False):
        return render(
            request,
            "vendors/offering_form.html",
            {
                "form": form,
                "vendor": vendor,
                "edit_mode": edit_mode,
            },
        )


class VendorOfferingArchiveView(LoginRequiredMixin, View):
    """Soft-delete (archive) an offering."""

    def post(self, request, pk):
        offering = get_object_or_404(
            VendorOffering,
            pk=pk,
            vendor__organization=request.user.organization,
        )
        archive_vendor_offering(offering)
        messages.success(request, f"Offering '{offering.name}' archived.")
        return redirect("vendors:vendor_detail", pk=offering.vendor.id)
