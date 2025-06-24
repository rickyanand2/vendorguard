from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from assessments.models import Assessment, Answer, Questionnaire, Question, Solution
from vendors.models import Vendor
from .forms import AssessmentForm, AnswerForm
from accounts.models import Organization
from django.contrib import messages

# for workflow
from workflow.utils import perform_transition
from workflow.models import WorkflowObject, Workflow
from django.http import HttpResponseBadRequest


@login_required
def start_assessment(request, solution_id):
    print(">>> [start_assessment] Called with solution_id:", solution_id)

    try:
        solution = get_object_or_404(Solution, id=solution_id)
        print(f">>> [start_assessment] Found solution: {solution}")

        vendor = solution.vendor
        print(f">>> [start_assessment] Found associated vendor: {vendor}")

        if hasattr(solution, "assessment"):
            print(">>> [start_assessment] Existing assessment found, redirecting.")
            return redirect(
                "assessments:assessment_detail", assessment_id=solution.assessment.id
            )
        org = request.user.membership.organization
        print(f">>> [start_assessment] Using organization: {org}")

        questionnaire = Questionnaire.objects.order_by("id").first()
        if not questionnaire:
            print("!!! [start_assessment] No questionnaire found.")
            messages.error(request, "No questionnaire template is available.")
            return redirect("vendors:vendor_list")

            # ✅ Check for existing Assessment to avoid unique constraint violation
        existing = Assessment.objects.filter(
            organization=org,
            solution=solution,
            questionnaire=questionnaire,
        ).first()

        if existing:
            print(">>> [start_assessment] Found existing assessment:", existing.id)
            messages.info(request, "Assessment already exists for this solution.")
            return redirect("assessments:assessment_detail", assessment_id=existing.id)

        assessment = Assessment.objects.create(
            solution=solution,
            organization=org,
            questionnaire=questionnaire,
        )
        print(f">>> [start_assessment] Created assessment: {assessment}")

        return redirect("assessments:assessment_detail", assessment_id=assessment.id)

    except Exception as e:
        print("!!! [start_assessment] Exception occurred:", str(e))
        messages.error(request, f"Failed to start assessment: {str(e)}")
        return redirect("vendors:vendor_list")


@login_required
def answer_questions(request, assessment_id):
    print(f">>> [answer_questions] Called with assessment_id: {assessment_id}")

    try:
        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            organization=request.user.membership.organization,
        )
        print(f">>> [answer_questions] Loaded assessment: {assessment}")

        questions = Question.objects.filter(questionnaire=assessment.questionnaire)
        print(f">>> [answer_questions] Loaded {questions.count()} questions")

        if request.method == "POST":
            print(">>> [answer_questions] Processing POST responses...")
            for question in questions:
                response = request.POST.get(f"response_{question.id}")
                if response:
                    Answer.objects.update_or_create(
                        assessment=assessment,
                        question=question,
                        defaults={"response": response},
                    )
                    print(f"    - Saved answer for question {question.id}: {response}")

            # Simple scoring logic
            total_weight = 0
            score = 0
            for question in questions:
                try:
                    answer = Answer.objects.get(
                        assessment=assessment, question=question
                    )
                    weight = question.weight or 1
                    total_weight += weight
                    if answer.response.lower() == "yes":
                        score += weight
                except Answer.DoesNotExist:
                    print(
                        f"!!! [answer_questions] No answer found for question {question.id}"
                    )

            assessment.status = "submitted"
            assessment.score = (score / total_weight) * 100 if total_weight else 0
            assessment.save()
            print(
                f">>> [answer_questions] Assessment saved with score: {assessment.score}"
            )
            return redirect(
                "assessments:assessment_detail", assessment_id=assessment.id
            )

        # GET request: load existing answers
        existing_answers = {
            ans.question.id: ans.response
            for ans in Answer.objects.filter(assessment=assessment)
        }
        print(">>> [answer_questions] Loaded existing answers:", existing_answers)

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
        print("!!! [answer_questions] Exception occurred:", str(e))
        messages.error(request, f"Unable to load assessment: {str(e)}")
        return redirect("vendors:vendor_list")


@login_required
def assessment_detail(request, assessment_id):
    """View a completed assessment and its answers."""

    print(">>> [assessment_detail] Called with id:", assessment_id)

    assessment = get_object_or_404(
        Assessment, id=assessment_id, organization=request.user.membership.organization
    )

    # 🛡️ Patch: Ensure workflow object exists (for older assessments)
    try:
        WorkflowObject.objects.get(
            content_type__model=assessment._meta.model_name,
            object_id=assessment.id,
        )
    except WorkflowObject.DoesNotExist:
        print("!!! [assessment_detail] No WorkflowObject found — attaching now.")
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


# For workflow
@login_required
def submit_for_review(request, assessment_id):
    try:
        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            organization=request.user.membership.organization,
        )

        # Perform transition
        success, message = perform_transition(
            obj=assessment,
            to_state_name="Review",
            user=request.user,
            comment="Submitted for review",
        )

        if not success:
            return HttpResponseBadRequest(f"Transition failed: {message}")

        messages.success(request, f"Assessment moved to 'Review' state.")
        return redirect("assessments:assessment_detail", assessment_id=assessment.id)

    except Exception as e:
        print(f"[submit_for_review] Error: {e}")
        return HttpResponseBadRequest("An unexpected error occurred.")
