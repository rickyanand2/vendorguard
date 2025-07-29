from trust.engine import calculate_vti


def update_vendor_trust_score(vendor):
    if hasattr(vendor, "trust_profile"):
        vendor.trust_profile.trust_score = calculate_vti(vendor)
        vendor.trust_profile.save()
