# Path: thirdparties/views.py
"""
FBV views for Third Parties and their Services/Solutions.

Rule of thumb:
- Always filter by `organization=request.user.organization`.
- On create, set `instance.organization = request.user.organization`.
- If the user somehow has no org, show a friendly error and bounce to Profile.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect

from services.services_thirdparties import (
    archive_thirdparty,
    archive_thirdparty_service,
    create_thirdparty_service,
    create_thirdparty_with_trust,
    update_thirdparty_service,
    update_thirdparty_with_trust,
    CrossTenantViolation,
)
from thirdparties.forms import (
    ThirdPartyForm,
    ThirdPartyServiceForm,
    ThirdPartyTrustProfileForm,
)
from thirdparties.models import ThirdParty, ThirdPartyService, ThirdPartyTrustProfile


def _org_or_bounce(request):
    """Return request.user.organization or send user to profile with a message."""
    org = getattr(request.user, "organization", None)
    if org is None:
        messages.error(
            request,
            "Please set your organization in Profile before using Third Parties.",
        )
        return None
    return org


def _archived_filter_for(model):
    return {"archived": False} if hasattr(model, "archived") else {}


# ─────────────────────────────────────────────
# Third Parties
# ─────────────────────────────────────────────


@login_required
def thirdparty_list(request):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    qs = ThirdParty.objects.filter(organization=org)
    f = _archived_filter_for(ThirdParty)
    if f:
        qs = qs.filter(**f)
    third_parties = qs.prefetch_related("services").order_by("-created_at")
    return render(
        request, "thirdparties/thirdparty_list.html", {"third_parties": third_parties}
    )


@login_required
def thirdparty_detail(request, pk):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    f = _archived_filter_for(ThirdParty)
    third_party = get_object_or_404(
        ThirdParty.objects.filter(organization=org, **f), pk=pk
    )

    sf = _archived_filter_for(ThirdPartyService)
    services_qs = third_party.services.all()
    if sf:
        services_qs = services_qs.filter(**sf)
    services = services_qs.exclude(id__isnull=True)

    return render(
        request,
        "thirdparties/thirdparty_detail.html",
        {"third_party": third_party, "services": services},
    )


@login_required
def thirdparty_create(request):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    if request.method == "POST":
        tp_form = ThirdPartyForm(request.POST)
        trust_form = ThirdPartyTrustProfileForm(request.POST)
        if tp_form.is_valid() and trust_form.is_valid():
            # Service will set organization from request.user.organization
            create_thirdparty_with_trust(request.user, tp_form, trust_form)
            messages.success(request, "Third party created successfully.")
            return redirect("thirdparties:thirdparty_list")
    else:
        tp_form = ThirdPartyForm()
        trust_form = ThirdPartyTrustProfileForm()

    return render(
        request,
        "thirdparties/thirdparty_form.html",
        {"form": tp_form, "trust_form": trust_form, "edit_mode": False},
    )


@login_required
def thirdparty_update(request, pk):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    third_party = get_object_or_404(ThirdParty, pk=pk, organization=org)
    trust_profile, _ = ThirdPartyTrustProfile.objects.get_or_create(
        third_party=third_party
    )

    if request.method == "POST":
        tp_form = ThirdPartyForm(request.POST, instance=third_party)
        trust_form = ThirdPartyTrustProfileForm(request.POST, instance=trust_profile)
        if tp_form.is_valid() and trust_form.is_valid():
            update_thirdparty_with_trust(third_party, tp_form, trust_form)
            messages.success(request, "Third party updated successfully.")
            return redirect("thirdparties:thirdparty_list")
    else:
        tp_form = ThirdPartyForm(instance=third_party)
        trust_form = ThirdPartyTrustProfileForm(instance=trust_profile)

    return render(
        request,
        "thirdparties/thirdparty_form.html",
        {"form": tp_form, "trust_form": trust_form, "edit_mode": True},
    )


@login_required
@csrf_protect
def thirdparty_archive(request, pk):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    if request.method == "POST":
        third_party = get_object_or_404(ThirdParty, pk=pk, organization=org)
        archive_thirdparty(third_party)
        messages.success(request, f"Third party '{third_party.name}' archived.")
    return redirect("thirdparties:thirdparty_list")


# ─────────────────────────────────────────────
# Services (“Solutions”)
# ─────────────────────────────────────────────


@login_required
def service_list(request):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    f = _archived_filter_for(ThirdPartyService)
    services = (
        ThirdPartyService.objects.filter(third_party__organization=org, **f)
        .select_related("third_party")
        .order_by("-created_at")
    )
    return render(request, "thirdparties/service_list.html", {"services": services})


@login_required
def service_detail(request, pk):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    service = get_object_or_404(ThirdPartyService, pk=pk, third_party__organization=org)
    return render(request, "thirdparties/service_detail.html", {"service": service})


@login_required
def service_create(request, thirdparty_id):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    third_party = get_object_or_404(ThirdParty, pk=thirdparty_id, organization=org)

    if request.method == "POST":
        form = ThirdPartyServiceForm(request.POST)
        if form.is_valid():
            try:
                create_thirdparty_service(third_party, request.user, form)
            except CrossTenantViolation:
                messages.error(
                    request,
                    "You cannot add a solution to a third party outside your organization.",
                )
            else:
                messages.success(request, f"Solution added to: {third_party.name}.")
                return redirect("thirdparties:service_list")
    else:
        form = ThirdPartyServiceForm()

    return render(
        request,
        "thirdparties/service_form.html",
        {"form": form, "third_party": third_party, "edit_mode": False},
    )


@login_required
def service_update(request, pk):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    service = get_object_or_404(ThirdPartyService, pk=pk, third_party__organization=org)

    if request.method == "POST":
        form = ThirdPartyServiceForm(request.POST, instance=service)
        if form.is_valid():
            update_thirdparty_service(service, form)
            messages.success(
                request, f"Solution updated for: {service.third_party.name}."
            )
            return redirect("thirdparties:service_list")
    else:
        form = ThirdPartyServiceForm(instance=service)

    return render(
        request,
        "thirdparties/service_form.html",
        {"form": form, "third_party": service.third_party, "edit_mode": True},
    )


@login_required
@csrf_protect
def service_archive(request, pk):
    org = _org_or_bounce(request)
    if org is None:
        return redirect("accounts:profile")

    if request.method == "POST":
        service = get_object_or_404(
            ThirdPartyService, pk=pk, third_party__organization=org
        )
        archive_thirdparty_service(service)
        messages.success(request, f"Solution '{service.name}' archived.")
        return redirect("thirdparties:thirdparty_detail", pk=service.third_party.pk)
