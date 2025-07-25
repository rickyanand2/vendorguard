# assessments/views.py

from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Assessment, Questionnaire, Question, VendorOffering, Vendor
from workflow.models import WorkflowObject, WorkflowLog  # Workflow import

from .forms import AssessmentForm, QuestionnaireForm, QuestionForm
from services.workflow import ensure_workflow_for_object
from services.assessments import (
    get_assessments_for_org,
    create_assessment_from_request,
    get_assessment_detail,
    submit_assessment_for_review,
    handle_answer_submission,
    get_questionnaire_context,
)

# ====================================================
# ✅ List of Questionnaire Views
# ====================================================


class QuestionnaireListView(ListView):
    model = Questionnaire
    template_name = "assessments/questionnaire_list.html"
    context_object_name = "questionnaires"


class QuestionnaireListView(ListView):
    model = Questionnaire
    template_name = "assessments/questionnaire_list.html"
    context_object_name = "questionnaires"


class QuestionnaireCreateView(CreateView):
    model = Questionnaire
    form_class = QuestionnaireForm
    template_name = "assessments/questionnaire_form.html"
    success_url = reverse_lazy("assessments:questionnaire_list")


class QuestionnaireDetailView(DetailView):
    model = Questionnaire
    template_name = "assessments/questionnaire_detail.html"
    context_object_name = "questionnaire"


# ====================================================
# ✅ List Assessments – Org-wide for logged-in user
# ====================================================
class AssessmentListView(LoginRequiredMixin, ListView):
    model = Assessment
    context_object_name = "assessments"
    template_name = "assessments/assessment_list.html"

    def get_queryset(self):
        return get_assessments_for_org(self.request.user.organization)


# ====================================================
# ✅ Create Assessment (Form POST)
# ====================================================
# assessments/views.py


class AssessmentCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        offering_id = request.GET.get("offering_id")
        questionnaire_id = request.GET.get("questionnaire_id")

        if not offering_id:
            return HttpResponseBadRequest(
                "Offering is required to create an assessment."
            )

        try:
            vendor_offering = VendorOffering.objects.get(id=offering_id)
        except VendorOffering.DoesNotExist:
            return HttpResponseBadRequest("Invalid offering.")

        # Default to NIST Questionnaire if none provided
        if not questionnaire_id:
            questionnaire = Questionnaire.objects.filter(name__icontains="NIST").first()
        else:
            questionnaire = Questionnaire.objects.filter(id=questionnaire_id).first()

        if not questionnaire:
            return HttpResponseBadRequest("No valid questionnaire found.")

        # Create the assessment
        assessment = Assessment.objects.create(
            organization=request.user.organization,
            created_by=request.user,
            vendor_offering=vendor_offering,
            questionnaire=questionnaire,
            status="draft",
        )

        return redirect("assessments:answer", pk=assessment.pk)


# ====================================================
# ✅ View Assessment Detail
# ====================================================
class AssessmentDetailView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = "assessments/assessment_detail.html"
    context_object_name = "assessment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object

        try:
            # Auto-create workflow if missing
            ensure_workflow_for_object(assessment)

            content_type = ContentType.objects.get_for_model(assessment.__class__)
            wf_obj = WorkflowObject.objects.get(
                content_type=content_type, object_id=assessment.pk
            )
            context["workflow_object"] = wf_obj
            context["workflow_logs"] = WorkflowLog.objects.filter(
                workflow_object=wf_obj
            ).select_related("user", "from_state", "to_state")
        except Exception as e:
            context["workflow_object"] = None
            context["workflow_logs"] = []
            print(f"[Workflow Attach Error]: {e}")

        return context


# ====================================================
# ✅ Submit Assessment for Review
# ====================================================
class SubmitAssessmentForReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        success, message = submit_assessment_for_review(request.user, pk)
        if success:
            messages.success(request, message)
            return redirect("assessments:detail", pk=pk)
        return HttpResponseBadRequest(message)


# ====================================================
# ✅ Answer Questionnaire View (GET + POST)
# ====================================================
class AnswerQuestionnaireView(LoginRequiredMixin, View):
    def get(self, request, pk):
        context = get_questionnaire_context(pk, request.user.organization)
        return render(request, "assessments/answer_questions.html", context)

    def post(self, request, pk):
        success, message = handle_answer_submission(
            request.user, pk, request.POST, request.FILES
        )
        if success:
            messages.success(request, message)
            return redirect("assessments:detail", pk=pk)
        messages.error(request, message)
        context = get_questionnaire_context(pk, request.user.organization)
        return render(request, "assessments/answer_questions.html", context)


class QuestionListView(ListView):
    model = Question
    template_name = "assessments/question_list.html"
    context_object_name = "questions"

    def get_queryset(self):
        return Question.objects.filter(is_archived=False)


class QuestionCreateView(CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "assessments/question_form.html"
    success_url = reverse_lazy("assessments:question_list")


class QuestionUpdateView(UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "assessments/question_form.html"
    success_url = reverse_lazy("assessments:question_list")


class QuestionArchiveView(View):
    def post(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        question.is_archived = True
        question.save()
        return redirect("assessments:question_list")
