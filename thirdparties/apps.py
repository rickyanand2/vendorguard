# thirdparties/apps.py
# --------------------
# Path: thirdparties/apps.py

from django.apps import AppConfig


class ThirdpartiesConfig(AppConfig):
    """
    Minimal AppConfig. Keep label == module name for predictable permission codenames
    (e.g., thirdparties.can_submit).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "thirdparties"
    verbose_name = "Third Parties (Suppliers & Service Providers)"
