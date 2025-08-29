# apps/workflow/management/commands/validate_workflows.py
"""
Validate workflow integrity and common pitfalls.

- Each workflow has exactly one initial state
- Each transition has >= 1 enabled guard (secure-by-default sanity)
- HAS_PERM guard codenames exist in auth_permission
"""

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError

from workflow.models import GuardType, State, Transition, Workflow


class Command(BaseCommand):
    help = "Validate workflows (initial state, guard presence, permission codenames)."

    def handle(self, *args, **options):
        errors: list[str] = []

        for wf in Workflow.objects.all():
            count_initial = State.objects.filter(workflow=wf, is_initial=True).count()
            if count_initial != 1:
                errors.append(
                    f"[{wf.name}] Initial state count must be exactly 1 (found {count_initial})."
                )

            for t in Transition.objects.filter(workflow=wf):
                enabled_guard_count = t.guard_rows.filter(enabled=True).count()
                if enabled_guard_count == 0:
                    errors.append(
                        f"[{wf.name}] Transition '{t.name}' has no enabled guards (will be denied)."
                    )

                for g in t.guard_rows.filter(enabled=True, type=GuardType.HAS_PERM):
                    perm = (g.params or {}).get("perm", "")
                    if "." not in perm:
                        errors.append(
                            f"[{wf.name}] Transition '{t.name}' HAS_PERM missing app_label or codename: '{perm}'"
                        )
                        continue
                    app_label, codename = perm.split(".", 1)
                    if not Permission.objects.filter(
                        content_type__app_label=app_label, codename=codename
                    ).exists():
                        errors.append(
                            f"[{wf.name}] Transition '{t.name}' HAS_PERM refers to unknown permission '{perm}'"
                        )

        if errors:
            for e in errors:
                self.stderr.write(f"ERROR: {e}")
            raise CommandError("Workflow validation failed.")
        self.stdout.write(self.style.SUCCESS("All workflows validate OK."))
