from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


# A reusable workflow definition (e.g., 'Assessment Lifecycle')
class Workflow(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# A discrete state in a workflow (e.g., 'Draft', 'Review', 'Approved')
class State(models.Model):
    workflow = models.ForeignKey(
        Workflow, related_name="states", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.workflow.name}: {self.name}"


# A permitted state change in a workflow (e.g., Draft → Review)
class Transition(models.Model):
    workflow = models.ForeignKey(
        Workflow, related_name="transitions", on_delete=models.CASCADE
    )
    from_state = models.ForeignKey(
        State, related_name="transitions_from", on_delete=models.CASCADE
    )
    to_state = models.ForeignKey(
        State, related_name="transitions_to", on_delete=models.CASCADE
    )
    role_required = models.CharField(
        max_length=100, blank=True, help_text="Optional role name"
    )

    name = models.CharField(
        max_length=100, help_text="Human-friendly name for this transition"
    )

    def __str__(self):
        return f"{self.from_state.name} ➜ {self.to_state.name} ({self.name})"


class WorkflowObjectManager(models.Manager):
    def get_for_instance(self, instance):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        return self.get(content_type=content_type, object_id=instance.pk)


# A generic link from a workflow to any model instance (e.g., Assessment)
class WorkflowObject(models.Model):
    objects = WorkflowObjectManager()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    current_state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.content_object} - {self.current_state.name if self.current_state else 'No State'}"


# An audit log entry for a transition on a workflow-enabled object
class WorkflowLog(models.Model):
    workflow_object = models.ForeignKey(
        WorkflowObject, related_name="logs", on_delete=models.CASCADE
    )
    from_state = models.ForeignKey(
        State, related_name="+", null=True, blank=True, on_delete=models.SET_NULL
    )
    to_state = models.ForeignKey(
        State, related_name="+", on_delete=models.SET_NULL, null=True
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.workflow_object} transitioned {self.from_state} → {self.to_state} by {self.user}"
