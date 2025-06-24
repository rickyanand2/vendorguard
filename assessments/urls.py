# assessments/urls.py
from django.urls import path
from . import views
from .views import submit_for_review  # For workflow

app_name = "assessments"

urlpatterns = [
    path("start/<int:solution_id>/", views.start_assessment, name="start_assessment"),
    path(
        "<int:assessment_id>/questions/",
        views.answer_questions,
        name="answer_questions",
    ),
    path("<int:assessment_id>/", views.assessment_detail, name="assessment_detail"),
    path(
        "<int:assessment_id>/submit/", submit_for_review, name="submit_for_review"
    ),  # For workflow
]
