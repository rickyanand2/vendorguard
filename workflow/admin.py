from django.contrib import admin

from .models import State, Transition, Workflow, WorkflowLog, WorkflowObject


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    inlines = []


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "workflow", "is_initial", "is_final")
    list_filter = ("workflow", "is_initial", "is_final")
    search_fields = ("name",)


@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    list_display = ("name", "workflow", "from_state", "to_state", "role_required")
    list_filter = ("workflow",)
    search_fields = ("name", "from_state__name", "to_state__name", "role_required")


@admin.register(WorkflowObject)
class WorkflowObjectAdmin(admin.ModelAdmin):
    list_display = ("content_object", "workflow", "current_state")
    list_filter = ("workflow", "current_state")
    readonly_fields = ("content_type", "object_id", "content_object")
    search_fields = ("content_type__model",)


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ("workflow_object", "from_state", "to_state", "user", "timestamp")
    list_filter = ("from_state", "to_state", "user")
    search_fields = ("workflow_object__content_object__id", "comment")
    readonly_fields = ("timestamp",)
