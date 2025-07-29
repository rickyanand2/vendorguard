# vendors/constants.py

from django.db import models


class OfferingType(models.TextChoices):
    PRODUCT = "product", "Product"
    SERVICE = "service", "Service"
    INTEGRATION = "integration", "Integration"
    # CONSULTING = "consulting", "Consulting" # ← optional future


class HostingType(models.TextChoices):
    CLOUD = "cloud", "Cloud"
    ON_PREMISE = "on_premise", "On-Premise"
    HYBRID = "hybrid", "Hybrid"


class DataType(models.TextChoices):
    PII = "pii", "Personally Identifiable Information"
    PHI = "phi", "Protected Health Information"
    PCI = "pci", "Payment Card Information"
    FINANCIAL = "financial", "Financial Records"
    BUSINESS = "business", "General Business Data"
    CREDENTIALS = "credentials", "Credentials / Passwords"
