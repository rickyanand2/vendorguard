# assessments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseBadRequest

from assessments.models import Assessment, Answer, Question
from workflow.models import WorkflowObject, Workflow


from services.assessments import (
    start_assessment_for_solution,
    submit_answers,
    transition_assessment_to_review,
    NoQuestionnaireError,
    AssessmentAlreadyExists,
)


# =========================
# Start Assessment View
# =========================
@login_required
def start_assessment(request, solution_id, org=None):
    try:
        assessment = start_assessment_for_solution(request.user, solution_id)
        messages.success(request, "Assessment started.")

    except NoQuestionnaireError:
        messages.error(request, "No questionnaire available.")
        return redirect("vendors:vendor_list")

    except AssessmentAlreadyExists as e:
        messages.info(request, "Assessment already exists.")
        assessment = e.existing_assessment

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("vendors:vendor_list")

    return redirect("assessments:assessment_detail", assessment_id=assessment.id)


# =========================


# =========================
# Answer Assessment View
# =========================
@login_required
def answer_questions(request, assessment_id):
    try:
        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            organization=request.user.membership.organization,
        )

        questions = Question.objects.filter(questionnaire=assessment.questionnaire)

        if request.method == "POST":
            submit_answers(request.user, assessment_id, request.POST)
            messages.success(request, "Assessment submitted.")
            return redirect(
                "assessments:assessment_detail", assessment_id=assessment.id
            )

        existing_answers = {
            ans.question.id: ans.response
            for ans in Answer.objects.filter(assessment=assessment)
        }

        return render(
            request,
            "assessments/answer_questions.html",
            {
                "assessment": assessment,
                "questions": questions,
                "answers": existing_answers,
            },
        )

    except Exception as e:
        messages.error(request, f"Unable to load assessment: {str(e)}")
        return redirect("vendors:vendor_list")


# =========================


# =========================
# Assessment Detail View
# =========================
@login_required
def assessment_detail(request, assessment_id, org):
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        organization=org,
    )

    try:
        WorkflowObject.objects.get(
            content_type__model=assessment._meta.model_name,
            object_id=assessment.id,
        )
    except WorkflowObject.DoesNotExist:
        workflow = Workflow.objects.get(name="Assessment Workflow")
        initial_state = workflow.states.filter(is_initial=True).first()
        WorkflowObject.objects.create(
            content_object=assessment,
            workflow=workflow,
            current_state=initial_state,
        )

    answers = Answer.objects.filter(assessment=assessment).select_related("question")

    return render(
        request,
        "assessments/assessment_detail.html",
        {
            "assessment": assessment,
            "answers": answers,
        },
    )


# =========================


# =========================
# Submit for Review (Workflow)
# =========================
@login_required
def submit_for_review(request, assessment_id):
    try:
        success, message, assessment = transition_assessment_to_review(
            request.user, assessment_id
        )

        if not success:
            return HttpResponseBadRequest(f"Transition failed: {message}")

        messages.success(request, "Assessment moved to 'Review' state.")
        return redirect("assessments:assessment_detail", assessment_id=assessment.id)

    except Exception as e:
        return HttpResponseBadRequest("An unexpected error occurred.")
