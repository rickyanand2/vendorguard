# assessments/views.py

from django.views import View
from django.views.generic import ListView, CreateView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Assessment
from .forms import AssessmentForm  # Create this if not already done
from services.assessments import (
    get_assessments_for_org,
    create_assessment_from_request,
    get_assessment_detail,
    submit_assessment_for_review,
    handle_answer_submission,
    get_questionnaire_context,
)


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
class AssessmentCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "assessments/assessment_form.html")

    def post(self, request):
        success, assessment, error = create_assessment_from_request(request)
        if success:
            messages.success(request, "Assessment created successfully.")
            return redirect("assessments:detail", pk=assessment.id)
        else:
            messages.error(request, error)
            return render(request, "assessments/assessment_form.html")


# ====================================================
# ✅ View Assessment Detail
# ====================================================
class AssessmentDetailView(LoginRequiredMixin, DetailView):
    model = Assessment
    context_object_name = "assessment"
    template_name = "assessments/assessment_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_context = get_assessment_detail(
            self.object.id, self.request.user.organization
        )
        context.update(detail_context)
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
        success, message = handle_answer_submission(request.user, pk, request.POST)
        if success:
            messages.success(request, "Answers submitted successfully.")
            return redirect("assessments:detail", pk=pk)
        messages.error(request, message)
        context = get_questionnaire_context(pk, request.user.organization)
        return render(request, "assessments/answer_questions.html", context)
