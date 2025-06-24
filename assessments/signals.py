# assessments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from assessments.models import Assessment
from workflow.models import Workflow, State, WorkflowObject


@receiver(post_save, sender=Assessment)
def attach_workflow_on_create(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        workflow = Workflow.objects.get(name="Assessment Workflow")
        initial_state = workflow.states.filter(is_initial=True).first()

        if not initial_state:
            print("!!! [Workflow Signal] No initial state for workflow.")
            return

        WorkflowObject.objects.create(
            content_object=instance,
            workflow=workflow,
            current_state=initial_state,
        )
        print(f">>> [Workflow Signal] Attached workflow to assessment {instance.id}")
    except Workflow.DoesNotExist:
        print("!!! [Workflow Signal] Assessment Workflow not found")
