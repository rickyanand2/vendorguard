# workflow/utils.py

from django.core.exceptions import PermissionDenied

from .models import Transition, WorkflowLog, WorkflowObject


# Transitions the object to a new state if a valid transition exists.
def perform_transition(content_object, user, to_state_name, comment=""):
    try:
        wo = WorkflowObject.objects.get(
            content_type__model=content_object._meta.model_name,
            object_id=content_object.id,
        )

        available_transitions = Transition.objects.filter(
            workflow=wo.workflow,
            from_state=wo.current_state,
            to_state__name=to_state_name,
        )

        if not available_transitions.exists():
            raise PermissionDenied(
                f"No transition from {wo.current_state} to {to_state_name}"
            )

        transition = available_transitions.first()

        WorkflowLog.objects.create(
            workflow_object=wo,
            from_state=wo.current_state,
            to_state=transition.to_state,
            user=user,
            comment=comment,
        )

        wo.current_state = transition.to_state
        wo.save()

        return True
    except WorkflowObject.DoesNotExist:
        raise ValueError("WorkflowObject not found for this content")
