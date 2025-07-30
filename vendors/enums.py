# vendors/constants.py

from django.db import models


class OfferingType(models.TextChoices):
    """Types of offerings a vendor can provide."""

    PRODUCT = "product", "Product"
    SERVICE = "service", "Service"
    INTEGRATION = "integration", "Integration"
    # CONSULTING = "consulting", "Consulting" # ← optional future


class HostingType(models.TextChoices):
    """Types of hosting environments a vendor may use."""

    CLOUD = "cloud", "Cloud"
    ON_PREMISE = "on_premise", "On-Premise"
    HYBRID = "hybrid", "Hybrid"
