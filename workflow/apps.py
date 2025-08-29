# apps/workflow/apps.py
from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    """
    VendorGuard Workflow Engine
    - DB-driven structure (Workflows/States/Transitions/Guards/Actions)
    - Execution logic is code (enums + dispatch tables) for a single, secure decision plane
    - No signals, no dynamic imports.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "workflow"
    verbose_name = "Workflow Engine"
