from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from assessments.models import Assessment  # target model

from .models import State, Workflow, WorkflowObject


@receiver(post_save, sender=Assessment)
def attach_workflow_to_assessment(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        # Fetch the assessment workflow
        workflow = Workflow.objects.get(name="Assessment Workflow")
        initial_state = workflow.states.get(is_initial=True)

        # Create workflow object
        WorkflowObject.objects.create(
            workflow=workflow,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            current_state=initial_state,
        )
        print(
            f"[Workflow] Attached '{workflow.name}' to assessment {instance.id} with initial state '{initial_state.name}'"
        )

    except Workflow.DoesNotExist:
        print("⚠️ [Workflow] 'Assessment Workflow' not found")
    except State.DoesNotExist:
        print("⚠️ [Workflow] Initial state not defined in workflow")
    except Exception as e:
        print(f"⚠️ [Workflow] Unexpected error: {e}")
