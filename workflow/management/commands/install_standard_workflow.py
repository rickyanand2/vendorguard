# apps/workflow/management/commands/install_standard_workflow.py
"""
Install a standard 4-state workflow with least-privilege guards.

States:
  - DRAFT (initial)
  - APPROVE
  - REJECT (final)
  - COMPLETE (final)

Transitions:
  - submit_for_approval  : DRAFT   -> APPROVE
  - request_changes      : APPROVE -> DRAFT
  - reject_from_draft    : DRAFT   -> REJECT
  - reject_from_approve  : APPROVE -> REJECT
  - complete_from_approve: APPROVE -> COMPLETE
  - complete_from_draft  : DRAFT   -> COMPLETE  (optional)

Guards (group 0): SAME_TENANT AND HAS_PERM('<app>.can_<verb>')
Actions: default NOOP (customize later in Admin)
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from workflow.models import (
    ActionType,
    GuardType,
    State,
    Transition,
    TransitionAction,
    TransitionGuard,
    Workflow,
)


def _perm(ns: str, codename: str) -> str:
    return f"{ns}.{codename}"


@transaction.atomic
def _install(
    flow_name: str,
    perm_ns: str,
    owner_required_on_submit: bool,
    include_complete_from_draft: bool,
):
    wf, _ = Workflow.objects.get_or_create(
        name=flow_name, defaults={"description": flow_name}
    )

    draft, _ = State.objects.get_or_create(
        workflow=wf, name="DRAFT", defaults={"is_initial": True}
    )
    approve, _ = State.objects.get_or_create(
        workflow=wf, name="APPROVE", defaults={"is_final": False}
    )
    reject, _ = State.objects.get_or_create(
        workflow=wf, name="REJECT", defaults={"is_final": True}
    )
    complete, _ = State.objects.get_or_create(
        workflow=wf, name="COMPLETE", defaults={"is_final": True}
    )

    # Ensure exactly one initial
    if not draft.is_initial:
        draft.is_initial = True
        draft.save(update_fields=["is_initial"])
    for s in (approve, reject, complete):
        if s.is_initial:
            s.is_initial = False
            s.save(update_fields=["is_initial"])

    # Transitions
    submit, _ = Transition.objects.get_or_create(
        workflow=wf,
        name="submit_for_approval",
        defaults={"source": draft, "target": approve},
    )
    changes, _ = Transition.objects.get_or_create(
        workflow=wf,
        name="request_changes",
        defaults={"source": approve, "target": draft},
    )
    r_d, _ = Transition.objects.get_or_create(
        workflow=wf,
        name="reject_from_draft",
        defaults={"source": draft, "target": reject},
    )
    r_a, _ = Transition.objects.get_or_create(
        workflow=wf,
        name="reject_from_approve",
        defaults={"source": approve, "target": reject},
    )
    c_a, _ = Transition.objects.get_or_create(
        workflow=wf,
        name="complete_from_approve",
        defaults={"source": approve, "target": complete},
    )
    c_d = None
    if include_complete_from_draft:
        c_d, _ = Transition.objects.get_or_create(
            workflow=wf,
            name="complete_from_draft",
            defaults={"source": draft, "target": complete},
        )

    def add_guard(
        t: Transition,
        kind: str,
        params: dict | None,
        group: int,
        order: int,
        name: str = "",
    ):
        TransitionGuard.objects.get_or_create(
            transition=t,
            type=kind,
            params=params or None,
            group=group,
            order=order,
            defaults={"enabled": True, "name": name or kind},
        )

    def add_action(
        t: Transition, kind: str, params: dict | None, order: int, name: str = ""
    ):
        TransitionAction.objects.get_or_create(
            transition=t,
            type=kind,
            params=params or None,
            order=order,
            defaults={"enabled": True, "name": name or kind},
        )

    # Guards (group 0): SAME_TENANT + HAS_PERM
    add_guard(submit, GuardType.SAME_TENANT, None, 0, 0, "same-tenant")
    add_guard(
        submit,
        GuardType.HAS_PERM,
        {"perm": _perm(perm_ns, "can_submit")},
        0,
        1,
        "perm: submit",
    )
    if owner_required_on_submit:
        add_guard(
            submit, GuardType.OBJECT_OWNER, {"attr": "created_by"}, 0, 2, "owner-only"
        )

    add_guard(changes, GuardType.SAME_TENANT, None, 0, 0, "same-tenant")
    add_guard(
        changes,
        GuardType.HAS_PERM,
        {"perm": _perm(perm_ns, "can_request_changes")},
        0,
        1,
        "perm: request_changes",
    )

    for t in (r_d, r_a):
        add_guard(t, GuardType.SAME_TENANT, None, 0, 0, "same-tenant")
        add_guard(
            t,
            GuardType.HAS_PERM,
            {"perm": _perm(perm_ns, "can_reject")},
            0,
            1,
            "perm: reject",
        )

    add_guard(c_a, GuardType.SAME_TENANT, None, 0, 0, "same-tenant")
    add_guard(
        c_a,
        GuardType.HAS_PERM,
        {"perm": _perm(perm_ns, "can_complete")},
        0,
        1,
        "perm: complete",
    )
    if c_d:
        add_guard(c_d, GuardType.SAME_TENANT, None, 0, 0, "same-tenant")
        add_guard(
            c_d,
            GuardType.HAS_PERM,
            {"perm": _perm(perm_ns, "can_complete")},
            0,
            1,
            "perm: complete",
        )

    # Default NOOP action (customize in Admin as needed)
    for t in filter(None, (submit, changes, r_d, r_a, c_a, c_d)):
        add_action(t, ActionType.NOOP, None, 0, "no-op")

    return wf


class Command(BaseCommand):
    help = "Install the standard 4-state workflow with least-privilege guards."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name", required=True, help="Workflow name (e.g., THIRDPARTY_DEFAULT)"
        )
        parser.add_argument(
            "--perm-ns", required=True, help="Permission namespace (e.g., thirdparty)"
        )
        parser.add_argument(
            "--owner-required-on-submit", action="store_true", default=False
        )
        parser.add_argument(
            "--no-complete-from-draft", action="store_true", default=False
        )

    def handle(self, *args, **opts):
        wf = _install(
            flow_name=opts["name"],
            perm_ns=opts["perm-ns"],
            owner_required_on_submit=opts["owner-required-on-submit"],
            include_complete_from_draft=not opts["no-complete-from-draft"],
        )
        self.stdout.write(self.style.SUCCESS(f"Installed/updated workflow '{wf.name}'"))
