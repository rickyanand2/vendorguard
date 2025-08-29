# workflow/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from assessments.models import Assessment
from services.services_workflow import (
    advance,
    get_or_create_workflow_object,
)
from workflow.models import Transition, Workflow


class SubmitAssessmentForReviewView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        assessment = get_object_or_404(Assessment, pk=pk)

        # STEP 1: Load the correct workflow (manually for now)
        workflow = Workflow.objects.get(name="Assessment Lifecycle")
        # STEP 2: Ensure WorkflowObject exists
        wf_obj = get_or_create_workflow_object(assessment, workflow)

        # STEP 3: Get valid transitions from current state
        transitions = Transition.objects.filter(
            workflow=workflow,
            from_state=wf_obj.current_state,
        )
        # STEP 4: Find transition to 'Review' state
        transition = next(
            (t for t in transitions if t.to_state.name.lower() == "review"), None
        )
        if not transition:
            return HttpResponseForbidden("No valid transition found.")

        # STEP 5: Apply the transition and update logs/state
        advance(request.user, assessment, transition)

        return redirect("assessments:assessment_detail", pk=pk)
