# services/assessments.py

from django.shortcuts import get_object_or_404
from assessments.models import Assessment, Questionnaire, Answer, Question
from vendors.models import VendorOffering
from workflow.models import Workflow, WorkflowObject
from django.db import transaction


# ===========================
# ✅ Get assessments by org
# ===========================
def get_assessments_for_org(org):
    """
    Fetch all assessments that belong to the user's organization.
    """
    return Assessment.objects.filter(organization=org).select_related(
        "questionnaire", "vendor_offering"
    )


# ===========================
# ✅ Create new assessment
# ===========================
def create_assessment_from_request(request):
    """
    Handles form submission for assessment creation.
    Expects POST data: questionnaire, vendor_offering
    """
    try:
        info_value = request.POST.get("info_value")
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
            info_value=info_value,
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
    """
    Fetch assessment, questions, and answers for detail view.
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
        "info_value": assessment.info_value,  # ⬅️ from model
    }


# ===========================
# ✅ Submit for Review Workflow
# ===========================
def submit_assessment_for_review(user, assessment_id):
    """
    Move assessment to 'Review' state using workflow engine.
    """
    try:
        assessment = get_object_or_404(
            Assessment, id=assessment_id, organization=user.organization
        )
        wf_obj = WorkflowObject.objects.get_for_model(assessment)

        next_state = wf_obj.workflow.states.filter(name="Review").first()
        if not next_state:
            return False, "Review state not found."

        wf_obj.current_state = next_state
        wf_obj.save()

        return True, "Assessment moved to review."

    except Exception as e:
        return False, f"Workflow error: {str(e)}"


# ===========================
# ✅ Submit answers (POST)
# ===========================
def handle_answer_submission(user, assessment_id, post_data):
    """
    Parse and save submitted answers for each question in the assessment.
    """
    try:
        assessment = get_object_or_404(
            Assessment, id=assessment_id, organization=user.organization
        )
        questions = Question.objects.filter(questionnaire=assessment.questionnaire)

        with transaction.atomic():
            for question in questions:
                key = f"question_{question.id}"
                response = post_data.get(key)
                if response is None:
                    continue  # Skipped question

                answer_obj, _ = Answer.objects.get_or_create(
                    assessment=assessment,
                    question=question,
                )
                answer_obj.response = response
                answer_obj.save()

        return True, "Answers submitted."

    except Exception as e:
        return False, f"Error saving answers: {str(e)}"


# ===========================
# ✅ Build context for Q&A form
# ===========================
def get_questionnaire_context(assessment_id, org):
    """
    Prepares the question-answer view context with form fields prefilled.
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, organization=org)
    questions = Question.objects.filter(questionnaire=assessment.questionnaire)

    existing_answers = {
        ans.question.id: ans.response
        for ans in Answer.objects.filter(assessment=assessment)
    }

    return {
        "assessment": assessment,
        "questions": questions,
        "answers": existing_answers,
    }
