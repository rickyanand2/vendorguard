# apps/workflow/models.py
"""
Data model for a small, auditable workflow engine.

Core idea:
- Structure lives in DB (Admin/fixtures): Workflow/State/Transition/TransitionGuard/TransitionAction
- Execution lives in code: enums + dispatch handlers (services/services_workflow.py)
- Guards implement OR-of-AND logic via (group, order)
- Actions are ordered DB-only side effects (safe/deterministic)
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q


# =============================================================================
# Enumerations for guard types and action types
# (Single decision plane: Admin can only choose among these safe, known options)
# =============================================================================


class GuardType(models.TextChoices):
    """Preconditions checked before a transition is allowed."""

    ALWAYS_ALLOW = "ALWAYS_ALLOW", "Always allow"
    ALWAYS_DENY = "ALWAYS_DENY", "Always deny"
    USER_SUPERUSER = "USER_SUPERUSER", "User is superuser"
    SAME_TENANT = (
        "SAME_TENANT",
        "User.tenant_id == Object.tenant_id (relaxed allow if either missing)",
    )
    HAS_PERM = (
        "HAS_PERM",
        "User has Django permission (params.perm='app_label.codename')",
    )
    IN_GROUPS = "IN_GROUPS", "User in any of params.groups"
    OBJECT_OWNER = "OBJECT_OWNER", "User == getattr(obj, params.attr or 'created_by')"
    FIELD_OP = (
        "FIELD_OP",
        "Compare obj.<path> via op (eq, ne, in, nin, contains, icontains, gte, lte, isnull)",
    )


class ActionType(models.TextChoices):
    """DB-only, synchronous post-effects executed after a transition succeeds."""

    NOOP = "NOOP", "No operation"
    SET_FIELD = "SET_FIELD", "Set obj.<field> = params.value"
    MIRROR_STATE = "MIRROR_STATE", "Mirror state name to obj.<field> with transform"
    APPEND_STATUS_SUFFIX = "APPEND_STATUS_SUFFIX", "Append suffix to obj.<field>"


# =============================================================================
# Structure tables
# =============================================================================


class Workflow(models.Model):
    """
    A named workflow definition (e.g., 'THIRDPARTY_DEFAULT', 'ASSESSMENT_DEFAULT').
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):  # pragma: no cover
        return self.name


class State(models.Model):
    """
    A discrete state in a workflow (e.g., DRAFT, APPROVE, REJECT, COMPLETE).

    One (and only one) initial state per workflow is enforced by a partial unique constraint
    (<= 1 at DB level) and validated by a management command (ensures exactly 1).
    """

    workflow = models.ForeignKey(
        Workflow, related_name="states", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    class Meta:
        unique_together = (("workflow", "name"),)
        indexes = [models.Index(fields=["workflow", "name"])]
        constraints = [
            # Enforce at most one initial state at DB level
            models.UniqueConstraint(
                fields=["workflow"],
                condition=Q(is_initial=True),
                name="uniq_initial_state_per_workflow",
            )
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.workflow.name}:{self.name}"


class Transition(models.Model):
    """
    A permitted move from source -> target inside a workflow.
    Guards and actions live as related rows.
    """

    workflow = models.ForeignKey(
        Workflow, related_name="transitions", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100, help_text="Unique within the workflow.")
    source = models.ForeignKey(State, on_delete=models.PROTECT, related_name="outgoing")
    target = models.ForeignKey(State, on_delete=models.PROTECT, related_name="incoming")

    class Meta:
        unique_together = (("workflow", "name"),)
        indexes = [
            models.Index(fields=["workflow", "name"]),
            models.Index(fields=["workflow", "source"]),
            models.Index(fields=["workflow", "target"]),
        ]

    def __str__(self):  # pragma: no cover
        return (
            f"{self.workflow.name}:{self.name} ({self.source.name}→{self.target.name})"
        )


class TransitionGuard(models.Model):
    """
    A guard row evaluated before a transition is allowed.

    Logic = OR-of-AND:
      - ALL enabled guards within the same group must pass (AND),
      - ANY passing group allows the transition (OR),
      - Secure default: ZERO enabled guards ⇒ DENY.

    params JSON depends on type; see handlers in services/services_workflow.py
    """

    transition = models.ForeignKey(
        Transition, related_name="guard_rows", on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="Label (for readability in Admin)."
    )
    type = models.CharField(max_length=32, choices=GuardType.choices)
    params = models.JSONField(
        null=True, blank=True, help_text="Optional JSON for guard configuration."
    )
    group = models.PositiveIntegerField(
        default=0, help_text="OR-group index; ALL in a group must pass."
    )
    order = models.PositiveSmallIntegerField(
        default=0, help_text="Ordering within group (cosmetic)."
    )
    negated = models.BooleanField(
        default=False, help_text="Invert the result of this guard."
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("group", "order", "id")
        indexes = [
            models.Index(fields=["transition", "group"]),
            models.Index(fields=["transition", "enabled"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.transition.name} ▸ guard[{self.group}:{self.order}] {self.type}"


class TransitionAction(models.Model):
    """
    Ordered actions executed after a transition succeeds.
    Keep effects simple and synchronous (DB-only, deterministic).
    """

    transition = models.ForeignKey(
        Transition, related_name="action_rows", on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="Label (for readability in Admin)."
    )
    type = models.CharField(max_length=32, choices=ActionType.choices)
    params = models.JSONField(
        null=True, blank=True, help_text="Optional JSON for action configuration."
    )
    order = models.PositiveSmallIntegerField(default=0)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")
        indexes = [
            models.Index(fields=["transition", "enabled"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.transition.name} ▸ action[{self.order}] {self.type}"


class WorkflowObject(models.Model):
    """
    Binds a workflow to ANY domain object via GenericForeignKey and stores current state.

    Privacy: we link to the subject using content_type/object_id, no data duplication.
    Safety: PROTECT on workflow/state to preserve history integrity.
    """

    workflow = models.ForeignKey(Workflow, on_delete=models.PROTECT)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    subject = GenericForeignKey("content_type", "object_id")

    current_state = models.ForeignKey(
        State, on_delete=models.PROTECT, related_name="current_for"
    )

    class Meta:
        unique_together = (("workflow", "content_type", "object_id"),)
        indexes = [
            models.Index(fields=["workflow", "content_type", "object_id"]),
            models.Index(fields=["current_state"]),
        ]

    def __str__(self):  # pragma: no cover
        subj = (
            self.subject
            if self.subject is not None
            else f"{self.content_type.app_label}.{self.content_type.model}:{self.object_id}"
        )
        return f"{self.workflow.name}:{subj}@{self.current_state.name}"


class WorkflowLog(models.Model):
    """
    Append-only audit log: who applied which transition, when, with minimal notes.

    - Keep PII out of notes.
    - on_delete=PROTECT to avoid losing audit history.
    """

    workflow_object = models.ForeignKey(
        WorkflowObject, related_name="logs", on_delete=models.PROTECT
    )
    action = models.CharField(max_length=64)  # transition name
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    notes = models.TextField(blank=True)
    at = models.DateTimeField()

    class Meta:
        ordering = ("-at", "-id")
        indexes = [
            models.Index(fields=["workflow_object", "at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.workflow_object} · {self.action} · {self.at}"
