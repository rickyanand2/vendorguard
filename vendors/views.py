from django.shortcuts import render, redirect
from .models import Vendor
from .forms import VendorForm, VendorTrustProfileForm, SolutionForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Membership
from .models import Vendor, VendorTrustProfile  # 🆕 import the trust profile model


@login_required
def vendor_list(request):
    org = Membership.objects.get(user=request.user).organization
    vendors = Vendor.objects.filter(organization=org)
    return render(request, "vendors/vendor_list.html", {"vendors": vendors})


@login_required
def vendor_add(request):

    org = Membership.objects.get(user=request.user).organization
    if request.method == "POST":
        # Debug statement
        print(">>> Received POST to vendor_create")

        form = VendorForm(request.POST)
        trust_form = VendorTrustProfileForm(request.POST)
        if form.is_valid() and trust_form.is_valid():
            vendor = form.save(commit=False)
            vendor.organization = org
            vendor.created_by = request.user
            vendor.save()

            # ✅ Trust profile
            trust_profile = trust_form.save(commit=False)
            trust_profile.vendor = vendor
            trust_profile.calculate_trust_score()
            trust_profile.save()

            return redirect("vendors:vendor_list")
    else:
        print(">>> Vendor form errors:", form.errors)
        print(">>> Trust form errors:", trust_form.errors)
        form = VendorForm()
        trust_form = VendorTrustProfileForm()
    return render(
        request,
        "vendors/vendor_form.html",
        {
            "form": form,
            "trust_form": trust_form,
        },
    )


@login_required
def vendor_edit(request, vendor_id):
    vendor = get_object_or_404(
        Vendor, id=vendor_id, organization=request.user.organization
    )

    # Get or create trust profile
    trust_profile, _ = VendorTrustProfile.objects.get_or_create(vendor=vendor)

    if request.method == "POST":
        vendor_form = VendorForm(request.POST, instance=vendor)
        trust_form = VendorTrustProfileForm(request.POST, instance=trust_profile)
        if vendor_form.is_valid() and trust_form.is_valid():
            vendor_form.save()
            trust = trust_form.save(commit=False)
            trust.calculate_trust_score()  # 🔁 optional: recalc on update
            trust.save()
            return redirect("vendors:vendor_list")
    else:
        vendor_form = VendorForm(instance=vendor)
        trust_form = VendorTrustProfileForm(instance=trust_profile)

    return render(
        request,
        "vendors/vendor_form.html",
        {"form": vendor_form, "trust_form": trust_form},
    )


@login_required
def vendor_archive(request, vendor_id):
    vendor = get_object_or_404(
        Vendor, id=vendor_id, organization=request.user.organization
    )
    vendor.archived = True
    vendor.save()
    return redirect("vendors:vendor_list")


@login_required
def add_solution(request, vendor_id):
    vendor = get_object_or_404(
        Vendor, id=vendor_id, organization=request.user.organization
    )
    if request.method == "POST":
        form = SolutionForm(request.POST)
        if form.is_valid():
            solution = form.save(commit=False)
            solution.vendor = vendor
            solution.save()
            return redirect("vendors:vendor_list")
    else:
        form = SolutionForm()
    return render(
        request, "vendors/solution_form.html", {"form": form, "vendor": vendor}
    )
