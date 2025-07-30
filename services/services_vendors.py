# services/services_vendors.py

from trust.engine import calculate_vendor_trust_score

# ─────────────────────────────────────────────
# 🔹 Vendor + Trust Logic
# ─────────────────────────────────────────────


def create_vendor_with_trust(user, vendor_form, trust_form):
    """Creates a vendor and trust profile, assigns org and creator,
    calculates initial trust score.
    """
    vendor = vendor_form.save(commit=False)
    vendor.organization = user.organization
    vendor.created_by = user
    vendor.save()

    trust = trust_form.save(commit=False)
    trust.vendor = vendor
    trust.trust_score = calculate_vendor_trust_score(vendor)
    trust.save()

    return vendor


def update_vendor_with_trust(vendor, vendor_form, trust_form):
    """Updates vendor and trust profile and recalculates trust score.
    """
    vendor_form.save()
    trust = trust_form.save(commit=False)
    trust.trust_score = calculate_vendor_trust_score(vendor)
    trust.save()
    return vendor


def archive_vendor(vendor):
    """Archives (soft-deletes) a vendor.
    """
    vendor.archived = True
    vendor.save()


# ─────────────────────────────────────────────
# 🔹 Vendor Offering Logic
# ─────────────────────────────────────────────


def create_vendor_offering(vendor, user, form):
    """Creates a new offering for the vendor.
    """
    offering = form.save(commit=False)
    offering.vendor = vendor
    offering.created_by = user
    offering.save()
    return offering


def update_vendor_offering(offering, form):
    """Updates an existing offering.
    """
    return form.save()


def archive_vendor_offering(offering):
    """Archives (soft-deletes) a vendor offering.
    """
    offering.archived = True
    offering.save()


# ─────────────────────────────────────────────
# 🔹 Recalculate Trust Score (On Demand)
# ─────────────────────────────────────────────


def update_vendor_score(vendor):
    """Recalculates and updates the vendor's trust score based on all assessed offerings.
    """
    trust_profile = vendor.trust_profile
    new_score = calculate_vendor_trust_score(vendor)

    if new_score is not None:
        trust_profile.trust_score = new_score
    else:
        trust_profile.trust_score = None  # No score if no valid assessments

    trust_profile.save()
