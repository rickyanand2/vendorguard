# assessments/urls.py

from django.urls import path
from .views import (
    AssessmentListView,
    AssessmentCreateView,
    AssessmentDetailView,
    SubmitAssessmentForReviewView,
    AnswerQuestionnaireView,
    QuestionnaireListView,
    QuestionnaireCreateView,
    QuestionnaireDetailView,
    QuestionCreateView,
    QuestionArchiveView,
    QuestionListView,
    QuestionUpdateView,
)

app_name = "assessments"

urlpatterns = [
    path("questionnaires/", QuestionnaireListView.as_view(), name="questionnaire_list"),
    path(
        "questionnaires/new/",
        QuestionnaireCreateView.as_view(),
        name="questionnaire_create",
    ),
    path(
        "questionnaires/create/",
        QuestionnaireCreateView.as_view(),
        name="questionnaire_create",
    ),
    path(
        "questionnaires/<int:pk>/",
        QuestionnaireDetailView.as_view(),
        name="questionnaire_detail",
    ),
    path("assessments/", AssessmentListView.as_view(), name="assessment_list"),
    path(
        "assessments/create/", AssessmentCreateView.as_view(), name="assessment_create"
    ),
    path("assessments/<int:pk>/", AssessmentDetailView.as_view(), name="detail"),
    path("questions/", QuestionListView.as_view(), name="question_list"),
    path("questions/new/", QuestionCreateView.as_view(), name="question_create"),
    path(
        "questions/<int:pk>/edit/", QuestionUpdateView.as_view(), name="question_edit"
    ),
    path(
        "questions/<int:pk>/archive/",
        QuestionArchiveView.as_view(),
        name="question_archive",
    ),
    path("", AssessmentListView.as_view(), name="list"),
    path("create/", AssessmentCreateView.as_view(), name="create"),
    path("<int:pk>/", AssessmentDetailView.as_view(), name="detail"),
    path("<int:pk>/submit/", SubmitAssessmentForReviewView.as_view(), name="submit"),
    path("<int:pk>/answer/", AnswerQuestionnaireView.as_view(), name="answer"),
    path(
        "assessments/<int:pk>/submit/",
        SubmitAssessmentForReviewView.as_view(),
        name="submit_for_review",
    ),
]
