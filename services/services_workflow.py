# services/services_workflow.py
"""
Workflow runtime services (KISS, single decision plane).

Public API:
  - ensure_workflow(obj, flow_name, user=None) -> WorkflowObject
  - available_transitions(user, obj, flow_name) -> List[Transition]
  - advance(obj, flow_name, transition_name, user, notes="", mirror_status=False, status_field="status") -> WorkflowObject

Security:
  - If a transition has ZERO enabled guard rows, it is DENIED (secure-by-default).
  - Only enum-based guard/action types are executable (no dynamic imports/registries).

Performance:
  - select_related + prefetch_related reduce per-call queries.
  - _run_actions batches field updates into a single save().
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import Any, Dict

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from workflow.models import (
    ActionType,
    GuardType,
    State,
    Transition,
    TransitionAction,
    TransitionGuard,
    Workflow,
    WorkflowLog,
    WorkflowObject,
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _p(d: dict, key: str, default=None):
    """Safe read from optional JSON params."""
    return (d or {}).get(key, default)


def _safe_getattr_path(obj: Any, path: str, max_depth: int = 4) -> Any:
    """
    Safe dotted traversal (e.g., "owner.email").
    - Depth-limited to avoid attribute walks
    - Disallows private attrs (leading underscore)
    - Returns None if any segment is missing.
    """
    if not path:
        return None
    cur = obj
    for depth, part in enumerate(path.split("."), 1):
        if depth > max_depth or not part or part.startswith("_"):
            return None
        cur = getattr(cur, part, None)
    return cur


# Field comparison operators for FIELD_OP guard
_OPS: Mapping[str, Callable[[Any, Any], bool]] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "contains": lambda a, b: isinstance(a, str) and isinstance(b, str) and (b in a),
    "icontains": lambda a, b: isinstance(a, str)
    and isinstance(b, str)
    and (b.lower() in a.lower()),
    "gte": lambda a, b: (a is not None and b is not None and a >= b),
    "lte": lambda a, b: (a is not None and b is not None and a <= b),
    "isnull": lambda a, b: (a is None) if bool(b) else (a is not None),
    "in": lambda a, b: a in (b or []),
    "nin": lambda a, b: a not in (b or []),
}

# -----------------------------------------------------------------------------
# Guard handlers (enum -> pure function)
# -----------------------------------------------------------------------------


def _g_allow(g: TransitionGuard, u, o) -> bool:
    return True


def _g_deny(g: TransitionGuard, u, o) -> bool:
    return False


def _g_superuser(g: TransitionGuard, u, o) -> bool:
    return bool(getattr(u, "is_superuser", False))


def _g_same_tenant(g: TransitionGuard, u, o) -> bool:
    u_tid = getattr(u, "tenant_id", None)
    o_tid = getattr(o, "tenant_id", None)
    # Relaxed allow if either is missing (no cross-tenant leak in typical setups)
    return True if (u_tid is None or o_tid is None) else (u_tid == o_tid)


def _g_has_perm(g: TransitionGuard, u, o) -> bool:
    perm = _p(g.params, "perm")
    return bool(perm and u.has_perm(perm))


def _g_in_groups(g: TransitionGuard, u, o) -> bool:
    want = set(_p(g.params, "groups", []) or [])
    have = set(u.groups.values_list("name", flat=True))
    return bool(want & have)


def _g_owner(g: TransitionGuard, u, o) -> bool:
    attr = _p(g.params, "attr", "created_by")
    return getattr(o, attr, None) == u


def _g_fieldop(g: TransitionGuard, u, o) -> bool:
    path = _p(g.params, "path")
    op = (_p(g.params, "op", "eq") or "eq").lower()
    val = _p(g.params, "value", None)
    cur = _safe_getattr_path(o, path)
    fn = _OPS.get(op)
    return bool(fn and fn(cur, val))


_GUARD_HANDLERS: Mapping[str, Callable[[TransitionGuard, Any, Any], bool]] = {
    GuardType.ALWAYS_ALLOW: _g_allow,
    GuardType.ALWAYS_DENY: _g_deny,
    GuardType.USER_SUPERUSER: _g_superuser,
    GuardType.SAME_TENANT: _g_same_tenant,
    GuardType.HAS_PERM: _g_has_perm,
    GuardType.IN_GROUPS: _g_in_groups,
    GuardType.OBJECT_OWNER: _g_owner,
    GuardType.FIELD_OP: _g_fieldop,
}


def _eval_guard(g: TransitionGuard, user, obj) -> bool:
    """
    Dispatch by enum type. Unknown type => handler is None => deny.
    Apply negation if requested.
    """
    handler = _GUARD_HANDLERS.get(g.type)
    ok = bool(handler and handler(g, user, obj))
    return (not ok) if g.negated else ok


def _guards_pass(t: Transition, user, obj) -> bool:
    """
    Evaluate OR-of-AND:
      - Group rows, ALL in group must pass (AND)
      - If ANY group passes, allow (OR)
    Secure default: if there are ZERO enabled guard rows, deny.
    """
    rows = list(t.guard_rows.filter(enabled=True).order_by("group", "order", "id"))
    if not rows:
        return False  # secure-by-default

    grouped = defaultdict(list)
    for r in rows:
        grouped[r.group].append(r)

    for _, members in grouped.items():
        # AND across members of a group
        if all(_eval_guard(r, user, obj) for r in members):
            return True
    return False


# -----------------------------------------------------------------------------
# Action handlers (enum -> function collecting updates for single save)
# -----------------------------------------------------------------------------


def _a_noop(
    a: TransitionAction, obj, user, notes, *, to_state: State, updates: dict[str, Any]
) -> None:
    return


def _a_set_field(
    a: TransitionAction, obj, user, notes, *, to_state: State, updates: dict[str, Any]
) -> None:
    fld = _p(a.params, "field")
    val = _p(a.params, "value")
    if fld and not fld.startswith("_") and hasattr(obj, fld):
        updates[fld] = val


def _a_mirror_state(
    a: TransitionAction, obj, user, notes, *, to_state: State, updates: dict[str, Any]
) -> None:
    fld = _p(a.params, "field", "status")
    tr = (_p(a.params, "transform", "upper") or "upper").lower()
    val = to_state.name or ""
    if tr == "upper":
        val = val.upper()
    elif tr == "lower":
        val = val.lower()
    if hasattr(obj, fld):
        updates[fld] = val


def _a_append_suffix(
    a: TransitionAction, obj, user, notes, *, to_state: State, updates: dict[str, Any]
) -> None:
    fld = _p(a.params, "field", "status")
    sfx = _p(a.params, "suffix", "")
    if hasattr(obj, fld):
        cur = getattr(obj, fld)
        if isinstance(cur, str):
            updates[fld] = f"{cur}{sfx}"


_ACTION_HANDLERS: Mapping[str, Callable[[TransitionAction, Any, Any, str], None]] = {
    ActionType.NOOP: _a_noop,
    ActionType.SET_FIELD: _a_set_field,
    ActionType.MIRROR_STATE: _a_mirror_state,
    ActionType.APPEND_STATUS_SUFFIX: _a_append_suffix,
}


def _run_actions(t: Transition, obj, user, notes: str, *, to_state: State) -> None:
    """
    Execute enabled actions in order, collecting field updates.
    Persist object with a single save() for efficiency and atomicity.
    """
    updates: Dict[str, Any] = {}
    for a in t.action_rows.filter(enabled=True).order_by("order", "id"):
        handler = _ACTION_HANDLERS.get(a.type)
        if handler:
            handler(a, obj, user, notes, to_state=to_state, updates=updates)

    if updates:
        for fld, val in updates.items():
            setattr(obj, fld, val)
        obj.save(update_fields=list(updates.keys()))


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


@transaction.atomic
def ensure_workflow(obj, *, flow_name: str, user=None) -> WorkflowObject:
    """
    Idempotently attach 'obj' to the named workflow at its initial state.

    Fails if:
      - Workflow doesn't exist
      - Workflow has no initial state
    """
    wf = Workflow.objects.filter(name=flow_name).first()
    if not wf:
        raise ValidationError(f"Workflow '{flow_name}' does not exist.")

    initial = State.objects.filter(workflow=wf, is_initial=True).first()
    if not initial:
        raise ValidationError(f"Workflow '{flow_name}' has no initial state.")

    ct = ContentType.objects.get_for_model(obj.__class__)
    wo, _ = WorkflowObject.objects.get_or_create(
        workflow=wf,
        content_type=ct,
        object_id=obj.pk,
        defaults={"current_state": initial},
    )
    return wo


def available_transitions(user, obj, *, flow_name: str) -> list[Transition]:
    """List transitions from the current state that pass guards for 'user'."""
    wo = ensure_workflow(obj, flow_name=flow_name, user=user)

    # Fetch candidates and related rows efficiently
    candidates = (
        Transition.objects.filter(workflow=wo.workflow, source=wo.current_state)
        .select_related("source", "target")
        .prefetch_related("guard_rows")
    )
    return [t for t in candidates if _guards_pass(t, user, obj)]


@transaction.atomic
def advance(
    obj,
    *,
    flow_name: str,
    transition_name: str,
    user,
    notes: str = "",
    mirror_status: bool = False,
    status_field: str = "status",
) -> WorkflowObject:
    """
    Perform a transition atomically:
      1) ensure binding exists
      2) lock the WorkflowObject row (prevents racey double-advance)
      3) locate transition by name within the workflow
      4) evaluate guards (secure-by-default)
      5) run ordered actions (DB-only)
      6) move state
      7) optionally mirror state name to obj.<status_field> (or use MIRROR_STATE)
      8) append audit log.
    """
    wo = ensure_workflow(obj, flow_name=flow_name, user=user)
    wo = WorkflowObject.objects.select_for_update().get(pk=wo.pk)

    try:
        t = (
            Transition.objects.select_related("source", "target")
            .prefetch_related("guard_rows", "action_rows")
            .get(workflow=wo.workflow, name=transition_name)
        )
    except Transition.DoesNotExist:
        raise ValidationError(  # noqa: B904
            f"Transition '{transition_name}' not found in workflow '{wo.workflow.name}'."
        )

    if t.source_id != wo.current_state_id:
        raise PermissionDenied(
            f"Transition '{transition_name}' not valid from state '{wo.current_state.name}'."
        )

    if not _guards_pass(t, user, obj):
        raise PermissionDenied("Transition not permitted by guards.")

    new_state = t.target

    _run_actions(t, obj, user, notes, to_state=new_state)

    wo.current_state = new_state
    wo.save(update_fields=["current_state"])

    if mirror_status and hasattr(obj, status_field):
        setattr(obj, status_field, new_state.name)
        obj.save(update_fields=[status_field])

    WorkflowLog.objects.create(
        workflow_object=wo,
        action=t.name,
        actor=user,
        notes=notes or "",
        at=timezone.now(),
    )
    return wo


# --------------------------------------------------------------------------------
# Backward-compatibility aliases (old API names used by legacy code)
# --------------------------------------------------------------------------------


def ensure_workflow_for_object(
    obj, workflow_name: str | None = None, *, flow_name: str | None = None, user=None
):
    """
    Legacy alias to 'ensure_workflow'.
    Accepts either 'workflow_name' (old) or 'flow_name' (new).
    """
    flow = flow_name or workflow_name
    if not flow:
        raise ValueError(
            "ensure_workflow_for_object requires 'flow_name' (or legacy 'workflow_name')."
        )
    return ensure_workflow(obj, flow_name=flow, user=user)


def get_available_transitions(
    user, obj, *, flow_name: str, workflow_name: str | None = None
):
    """
    Legacy alias to 'available_transitions'.
    Accepts legacy 'workflow_name'.
    """
    return available_transitions(user, obj, flow_name=flow_name or workflow_name)


def apply_transition(
    obj,
    *,
    flow_name: str | None = None,
    workflow_name: str | None = None,
    transition: str | None = None,
    transition_name: str | None = None,
    user=None,
    notes: str = "",
    mirror_status: bool = False,
    status_field: str = "status",
):
    """
    Legacy alias to 'advance'.
    Accepts:
      - 'workflow_name' (old) or 'flow_name' (new)
      - 'transition' (old) or 'transition_name' (new).
    """
    flow = flow_name or workflow_name
    name = transition_name or transition
    if not flow or not name:
        raise ValueError(
            "apply_transition requires both a flow name and a transition name."
        )
    return advance(
        obj,
        flow_name=flow,
        transition_name=name,
        user=user,
        notes=notes,
        mirror_status=mirror_status,
        status_field=status_field,
    )
