# apps/workflow/admin.py
"""
Admin UI to manage workflow structure and operate workflow objects.

- Define Workflow/State/Transition
- Configure TransitionGuard (OR-of-AND) and TransitionAction (ordered) via inlines
- Operate WorkflowObject via bulk actions (show transitions / safe advance)
"""

from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

from services.services_workflow import advance, available_transitions
from workflow.models import (
    State,
    Transition,
    TransitionAction,
    TransitionGuard,
    Workflow,
    WorkflowLog,
    WorkflowObject,
)


def _subject_admin_link(wo: WorkflowObject) -> str:
    """Try to link back to the subject admin page, fall back to str()."""
    try:
        ct: ContentType = wo.content_type
        url = reverse(f"admin:{ct.app_label}_{ct.model}_change", args=[wo.object_id])
        return format_html('<a href="{}">{}</a>', url, str(wo.subject))
    except NoReverseMatch:
        return str(wo.subject)


class GuardInline(admin.TabularInline):
    model = TransitionGuard
    extra = 0
    fields = ("enabled", "group", "order", "name", "type", "params", "negated")
    show_change_link = False


class ActionInline(admin.TabularInline):
    model = TransitionAction
    extra = 0
    fields = ("enabled", "order", "name", "type", "params")
    show_change_link = False


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("id", "workflow", "name", "is_initial", "is_final")
    list_filter = ("workflow", "is_initial", "is_final")
    search_fields = ("name",)


@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    """
    Secure defaults:
      - A transition with ZERO enabled guards is DENIED by the engine.
      - Common baseline: group 0 → SAME_TENANT + HAS_PERM('app.codename').
    """

    list_display = ("id", "workflow", "name", "source", "target")
    list_filter = ("workflow",)
    search_fields = ("name",)
    inlines = (GuardInline, ActionInline)


@admin.register(WorkflowObject)
class WorkflowObjectAdmin(admin.ModelAdmin):
    """
    For operators:
      - "Show available transitions" (for the current admin user)
      - "Advance if exactly one transition is available" (safety-first).
    """

    list_display = (
        "id",
        "workflow",
        "content_type",
        "object_id",
        "subject_link",
        "current_state",
    )
    list_filter = ("workflow", "current_state", "content_type")
    search_fields = ("object_id",)
    readonly_fields = ("subject_link",)
    actions = ("action_show_available", "action_advance_single")

    def subject_link(self, obj):
        return _subject_admin_link(obj)

    subject_link.short_description = "Subject"

    def has_delete_permission(self, request, obj=None):
        return False  # preserve audit trail

    @admin.action(description="Show available transitions (for YOU)")
    def action_show_available(self, request, queryset):
        for wo in queryset:
            try:
                subs = available_transitions(
                    request.user, wo.subject, flow_name=wo.workflow.name
                )
                names = ", ".join(t.name for t in subs) or "None"
                self.message_user(
                    request,
                    f"WO#{wo.id} @ {wo.current_state.name}: {names}",
                    level=messages.INFO,
                )
            except Exception as e:
                self.message_user(request, f"WO#{wo.id}: {e}", level=messages.ERROR)

    @admin.action(description="Advance if exactly one transition is available")
    def action_advance_single(self, request, queryset):
        moved = 0
        for wo in queryset:
            try:
                subs = available_transitions(
                    request.user, wo.subject, flow_name=wo.workflow.name
                )
                if len(subs) == 1:
                    advance(
                        wo.subject,
                        flow_name=wo.workflow.name,
                        transition_name=subs[0].name,
                        user=request.user,
                        notes="admin",
                        mirror_status=True,  # mirrors state name to 'status' field if present
                    )
                    moved += 1
                else:
                    self.message_user(
                        request,
                        f"WO#{wo.id}: {'no' if not subs else 'multiple'} transitions; skipped.",
                        level=messages.WARNING,
                    )
            except Exception as e:
                self.message_user(request, f"WO#{wo.id}: {e}", level=messages.ERROR)
        if moved:
            self.message_user(
                request, f"Advanced {moved} object(s).", level=messages.SUCCESS
            )


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ("id", "workflow_object", "action", "actor", "at")
    list_filter = ("action", "actor")
    date_hierarchy = "at"

    def has_delete_permission(self, request, obj=None):
        return False  # append-only in Admin
