from django import forms
from .models import Assessment, Answer


class AssessmentForm(forms.ModelForm):
    """Form for creating or updating an Assessment."""

    class Meta:
        model = Assessment
        fields = ["solution", "questionnaire"]
        widgets = {
            "solution": forms.Select(attrs={"class": "form-control"}),
            "questionnaire": forms.Select(attrs={"class": "form-control"}),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["answer", "response", "comments"]
        widgets = {
            "answer": forms.Select(
                choices=Answer.ANSWER_CHOICES, attrs={"class": "form-select"}
            ),
            "response": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
        labels = {"response": "Your Answer"}


class InlineAnswerForm(forms.ModelForm):
    """
    Optional: Used for displaying answers inline with questions (e.g., in HTMX forms)
    """

    class Meta:
        model = Answer
        fields = ["response", "risk_impact"]
        widgets = {
            "response": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "risk_impact": forms.NumberInput(
                attrs={"class": "form-control", "step": 0.1}
            ),
        }
