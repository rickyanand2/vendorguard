# vendors/constants.py

from django.db import models


class OfferingType(models.TextChoices):
    PRODUCT = "product", "Product"
    SERVICE = "service", "Service"
    INTEGRATION = "integration", "Integration"
    # CONSULTING = "consulting", "Consulting" # ← optional future
