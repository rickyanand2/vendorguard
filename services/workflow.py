# services/workflow.py

from workflow.models import WorkflowObject, Transition, WorkflowLog, State, Workflow
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied


def get_workflow_object(obj):
    """
    Returns the WorkflowObject instance for the given model instance.
    """
    return WorkflowObject.objects.get_for_instance(obj)


def get_or_create_workflow_object(obj, workflow):
    """
    Ensures the object has an associated WorkflowObject.
    If missing, creates one using the workflow's initial state.
    Requires the workflow object to already exist.
    """
    content_type = ContentType.objects.get_for_model(obj.__class__)
    initial_state = workflow.states.filter(is_initial=True).first()

    if not initial_state:
        raise ValueError(f"Workflow '{workflow.name}' has no initial state defined.")

    wf_obj, created = WorkflowObject.objects.get_or_create(
        content_type=content_type,
        object_id=obj.pk,
        defaults={
            "workflow": workflow,
            "current_state": initial_state,
        },
    )
    return wf_obj


def ensure_workflow_for_object(obj, workflow_name="Assessment Workflow"):
    """
    Ensure the given object has an associated WorkflowObject.
    If missing, attach it using the workflow's initial state.
    """
    content_type = ContentType.objects.get_for_model(obj.__class__)

    # Use first() instead of get() to avoid MultipleObjectsReturned
    workflow = Workflow.objects.filter(name=workflow_name).first()
    if not workflow:
        raise Workflow.DoesNotExist(f"Workflow '{workflow_name}' does not exist.")

    initial_state = workflow.states.filter(is_initial=True).first()
    if not initial_state:
        raise State.DoesNotExist(f"No initial state for workflow '{workflow_name}'.")

    wf_obj, created = WorkflowObject.objects.get_or_create(
        content_type=content_type,
        object_id=obj.pk,
        defaults={
            "workflow": workflow,
            "current_state": initial_state,
        },
    )

    return wf_obj


def get_available_transitions(user, obj):
    """
    Returns a list of valid transitions from the object's current state,
    optionally filtered by the user's role.
    """
    wf_obj = get_workflow_object(obj)
    transitions = Transition.objects.filter(
        workflow=wf_obj.workflow,
        from_state=wf_obj.current_state,
    )

    return [
        t
        for t in transitions
        if not t.role_required or getattr(user, "role", "") == t.role_required
    ]


def apply_transition(user, obj, transition: Transition, comment=""):
    """
    Applies the given transition to the object:
    - Moves it to the next state.
    - Updates the WorkflowObject and optionally the model's 'status' field.
    - Creates a WorkflowLog entry.
    """
    content_type = ContentType.objects.get_for_model(obj.__class__)
    wf_obj = WorkflowObject.objects.get(content_type=content_type, object_id=obj.pk)

    if wf_obj.current_state != transition.from_state:
        raise PermissionDenied("Transition doesn't match current state.")

    # Apply transition
    wf_obj.current_state = transition.to_state
    wf_obj.save()

    # Optionally update the object's status field
    if hasattr(obj, "status"):
        obj.status = transition.to_state.name.lower()
        obj.save()

    # Log the transition
    WorkflowLog.objects.create(
        workflow_object=wf_obj,
        from_state=transition.from_state,
        to_state=transition.to_state,
        user=user,
        comment=comment,
    )

    return wf_obj.current_state
