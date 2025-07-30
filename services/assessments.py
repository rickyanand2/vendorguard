# services/assessments.py

from django.shortcuts import get_object_or_404

from assessments.constants import AnswerChoices
from assessments.models import Answer, Assessment, Questionnaire
from services.workflow import (
    apply_transition,
    ensure_workflow_for_object,
    get_available_transitions,
)
from vendors.models import VendorOffering
from workflow.models import Workflow, WorkflowObject


# ===========================
# ✅ Get assessments by org
# ===========================
def get_assessments_for_org(org):
    """Fetch all assessments that belong to the user's organization."""
    return Assessment.objects.filter(organization=org).select_related(
        "questionnaire", "vendor_offering"
    )


# ===========================
# ✅ Create new assessment
# ===========================
def create_assessment_from_request(request):
    """Handles form submission for assessment creation.
    Expects POST data: questionnaire, vendor_offering.
    """
    try:
        info_value = request.POST.get("information_value")
        risk_level = request.POST.get("risk_level")
        questionnaire_id = request.POST.get("questionnaire")
        offering_id = request.POST.get("vendor_offering")

        if not questionnaire_id or not offering_id:
            return False, None, "Both Questionnaire and Offering are required."

        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
        offering = get_object_or_404(
            VendorOffering,
            id=offering_id,
            vendor__organization=request.user.organization,
        )

        # Prevent duplicates (optional)
        existing = Assessment.objects.filter(
            organization=request.user.organization,
            questionnaire=questionnaire,
            vendor_offering=offering,
        ).first()
        if existing:
            return True, existing, "Assessment already exists. Redirecting..."

        assessment = Assessment.objects.create(
            questionnaire=questionnaire,
            vendor_offering=offering,
            organization=request.user.organization,
            information_value=info_value,
            risk_level=risk_level,
        )

        # Automatically create workflow object
        workflow = Workflow.objects.get(name="Assessment Workflow")
        initial_state = workflow.states.filter(is_initial=True).first()
        WorkflowObject.objects.create(
            content_object=assessment,
            workflow=workflow,
            current_state=initial_state,
        )

        return True, assessment, None

    except Exception as e:
        return False, None, f"Error creating assessment: {str(e)}"


# ===========================
# ✅ Get context for detail view
# ===========================
def get_assessment_detail(assessment_id, org):
    """Fetch assessment, questions, and answers for detail view.
    Now includes recommended risk level and information value.
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, organization=org)
    answers = Answer.objects.filter(assessment=assessment).select_related("question")
    questions = assessment.questionnaire.questions.all()

    return {
        "assessment": assessment,
        "answers": answers,
        "questions": questions,
        "recommended_risk": assessment.recommended_risk_level,  # ⬅️ from model
        "info_value": assessment.information_value,  # ⬅️ from model
    }


# ===========================
# ✅ Submit for Review Workflow
# ===========================
def submit_assessment_for_review(user, pk):
    from assessments.models import Assessment  # prevent circular import

    try:
        assessment = Assessment.objects.get(pk=pk)

        # Ensure workflow exists
        ensure_workflow_for_object(assessment)

        # Check transitions
        transitions = get_available_transitions(user, assessment)
        transition = next(
            (t for t in transitions if t.to_state.name.lower() == "review"),
            None,
        )

        if not transition:
            return False, "No valid transition to 'Review' available."

        apply_transition(user, assessment, transition, comment="Submitted for review.")
        return True, "Assessment submitted for review."
    except Assessment.DoesNotExist:
        return False, "Assessment not found."
    except Exception as e:
        return False, str(e)


# ===========================
# ✅ Submit answers (POST)
# ===========================
def handle_answer_submission(user, assessment_id, post_data, files=None):
    try:
        assessment = Assessment.objects.get(
            id=assessment_id, organization=user.organization
        )
        questionnaire = assessment.questionnaire
        questions = questionnaire.questions.filter(is_archived=False)

        for question in questions:
            prefix = f"q_{question.id}"
            response = post_data.get(f"{prefix}_response")
            supporting_text = post_data.get(f"{prefix}_supporting_text", "")
            comments = post_data.get(f"{prefix}_comments", "")
            evidence = files.get(f"{prefix}_evidence") if files else None

            if response:
                Answer.objects.update_or_create(
                    assessment=assessment,
                    question=question,
                    defaults={
                        "response": response,
                        "supporting_text": supporting_text,
                        "comments": comments,
                        "evidence": evidence,
                    },
                )
        return True, "Answers submitted successfully."
    except Exception as e:
        return False, str(e)


# ===========================
# ✅ Build context for Q&A form
# ===========================
def get_questionnaire_context(assessment_id, organization):
    assessment = Assessment.objects.get(id=assessment_id, organization=organization)
    questionnaire = assessment.questionnaire
    questions = questionnaire.questions.filter(is_archived=False)

    context = {
        "assessment": assessment,
        "questions": questions,
        "answer_choices": AnswerChoices.choices,
    }
    return context
