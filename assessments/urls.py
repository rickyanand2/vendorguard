# assessments/urls.py

from django.urls import path
from .views import (
    AssessmentListView,
    AssessmentCreateView,
    AssessmentDetailView,
    SubmitAssessmentForReviewView,
    AnswerQuestionnaireView,
)

app_name = "assessments"

urlpatterns = [
    path("", AssessmentListView.as_view(), name="list"),
    path("create/", AssessmentCreateView.as_view(), name="create"),
    path("<int:pk>/", AssessmentDetailView.as_view(), name="detail"),
    path("<int:pk>/submit/", SubmitAssessmentForReviewView.as_view(), name="submit"),
    path("<int:pk>/answer/", AnswerQuestionnaireView.as_view(), name="answer"),
]
