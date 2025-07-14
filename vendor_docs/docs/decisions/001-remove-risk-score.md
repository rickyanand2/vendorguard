# ADR 001: Remove Trust Score from Final Product

## Date
2025-06-27

## Decision
VendorGuard will no longer calculate a unified "Trust Score" for vendors.
Instead, it will provide decision support tools for users to assess risk contextually.

## Reasoning
- Risk is subjective per org; automated scoring could mislead.
- MVP focus is to accelerate due diligence, not replace judgment.
- Offers more flexibility and aligns with modern GRC practices.

## Impact
- Deprecated `calculate_trust_score` and `calculate_aggregate_vendor_risk_score`.
- TrustProfile fields retained for reference.
- Assessment scoring remains per question (if needed), not aggregated.

## Status
Accepted, implemented 2025-06-27.
