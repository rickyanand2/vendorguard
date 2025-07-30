# vendors/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect

from services.services_vendors import (
    archive_vendor,
    archive_vendor_offering,
    create_vendor_offering,
    create_vendor_with_trust,
    update_vendor_offering,
    update_vendor_with_trust,
)
from vendors.forms import VendorForm, VendorOfferingForm, VendorTrustProfileForm
from vendors.models import Vendor, VendorOffering, VendorTrustProfile

# ─────────────────────────────────────────────
# 🔹 Vendor Views
# ─────────────────────────────────────────────


@login_required
def vendor_list(request):
    """Show all active (non-archived) vendors for the current organization.
    """
    vendors = (
        Vendor.objects.prefetch_related("offerings")
        .filter(organization=request.user.organization, archived=False)
        .order_by("-created_at")
    )

    return render(request, "vendors/vendor_list.html", {"vendors": vendors})


@login_required
def vendor_detail(request, pk):
    """Show details of a specific vendor including offerings.
    """
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


@login_required
def vendor_create(request):
    """Create a new vendor with trust profile.
    """
    if request.method == "POST":
        vendor_form = VendorForm(request.POST)
        trust_form = VendorTrustProfileForm(request.POST)

        if vendor_form.is_valid() and trust_form.is_valid():
            create_vendor_with_trust(request.user, vendor_form, trust_form)
            messages.success(request, "Vendor created successfully.")
            return redirect("vendors:vendor_list")
    else:
        vendor_form = VendorForm()
        trust_form = VendorTrustProfileForm()

    return render(
        request,
        "vendors/vendor_form.html",
        {
            "form": vendor_form,
            "trust_form": trust_form,
            "edit_mode": False,
        },
    )


@login_required
def vendor_update(request, pk):
    """Update an existing vendor and trust profile.
    """
    vendor = get_object_or_404(Vendor, pk=pk, organization=request.user.organization)
    trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)

    if request.method == "POST":
        vendor_form = VendorForm(request.POST, instance=vendor)
        trust_form = VendorTrustProfileForm(request.POST, instance=trust_profile)

        if vendor_form.is_valid() and trust_form.is_valid():
            update_vendor_with_trust(vendor, vendor_form, trust_form)
            messages.success(request, "Vendor updated successfully.")
            return redirect("vendors:vendor_list")
    else:
        vendor_form = VendorForm(instance=vendor)
        trust_form = VendorTrustProfileForm(instance=trust_profile)

    return render(
        request,
        "vendors/vendor_form.html",
        {
            "form": vendor_form,
            "trust_form": trust_form,
            "edit_mode": True,
        },
    )


@login_required
@csrf_protect
def vendor_archive(request, pk):
    """Soft-delete (archive) a vendor.
    """
    if request.method == "POST":
        vendor = get_object_or_404(
            Vendor, pk=pk, organization=request.user.organization
        )
        archive_vendor(vendor)
        messages.success(request, f"Vendor '{vendor.name}' archived.")
    return redirect("vendors:vendor_list")


# ─────────────────────────────────────────────
# 🔹 Vendor Offering Views
# ─────────────────────────────────────────────


@login_required
def offering_list(request):
    """Show all active offerings under the current organization.
    """
    offerings = (
        VendorOffering.objects.filter(
            vendor__organization=request.user.organization, archived=False
        )
        .select_related("vendor")
        .order_by("-created_at")
    )

    return render(request, "vendors/offering_list.html", {"offerings": offerings})


@login_required
def offering_detail(request, pk):
    """Show detail for a single offering.
    """
    offering = get_object_or_404(
        VendorOffering, pk=pk, vendor__organization=request.user.organization
    )
    return render(request, "vendors/offering_detail.html", {"offering": offering})


@login_required
def offering_create(request, vendor_id):
    """Create a new offering under a vendor.
    """
    vendor = get_object_or_404(
        Vendor, pk=vendor_id, organization=request.user.organization
    )

    if request.method == "POST":
        form = VendorOfferingForm(request.POST)
        if form.is_valid():
            create_vendor_offering(vendor, request.user, form)
            messages.success(request, f"Offering added to Vendor: {vendor.name}.")
            return redirect("vendors:offering_list")
    else:
        form = VendorOfferingForm()

    return render(
        request,
        "vendors/offering_form.html",
        {
            "form": form,
            "vendor": vendor,
            "edit_mode": False,
        },
    )


@login_required
def offering_update(request, pk):
    """Update an existing vendor offering.
    """
    offering = get_object_or_404(
        VendorOffering, pk=pk, vendor__organization=request.user.organization
    )

    if request.method == "POST":
        form = VendorOfferingForm(request.POST, instance=offering)
        if form.is_valid():
            update_vendor_offering(offering, form)
            messages.success(
                request, f"Offering updated for Vendor: {offering.vendor.name}."
            )
            return redirect("vendors:offering_list")
    else:
        form = VendorOfferingForm(instance=offering)

    return render(
        request,
        "vendors/offering_form.html",
        {
            "form": form,
            "vendor": offering.vendor,
            "edit_mode": True,
        },
    )


@login_required
@csrf_protect
def offering_archive(request, pk):
    """Soft-delete (archive) an offering.
    """
    if request.method == "POST":
        offering = get_object_or_404(
            VendorOffering, pk=pk, vendor__organization=request.user.organization
        )
        archive_vendor_offering(offering)
        messages.success(request, f"Offering '{offering.name}' archived.")
        return redirect("vendors:vendor_detail", pk=offering.vendor.pk)
