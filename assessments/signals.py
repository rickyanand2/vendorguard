# assessments/signals.py
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from assessments.models import Assessment
from workflow.models import State, Workflow, WorkflowObject


@receiver(post_save, sender=Assessment)
def attach_workflow_on_create(sender, instance, created, **kwargs):
    if not created:
        return  # Only run on creation

    # Prevent duplicate bindings
    if WorkflowObject.objects.filter(
        content_type=ContentType.objects.get_for_model(Assessment),
        object_id=instance.pk,
    ).exists():
        return

    try:
        # Get the default workflow (adjust name as needed)
        workflow = Workflow.objects.get(name="Assessment Workflow")

        # Get initial state
        initial_state = State.objects.get(workflow=workflow, is_initial=True)

        if not initial_state:
            print("!!! [Workflow Signal] No initial state for workflow.")
            return

        # Bind workflow to this assessment
        WorkflowObject.objects.create(
            workflow=workflow,
            content_type=ContentType.objects.get_for_model(Assessment),
            object_id=instance.pk,
            current_state=initial_state,
        )
    except (Workflow.DoesNotExist, State.DoesNotExist) as e:
        # Log or silently fail
        print(f"Workflow auto-binding skipped: {e}")
