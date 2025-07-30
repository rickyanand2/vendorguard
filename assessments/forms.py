# assessments/forms.py

from django import forms
from taggit.forms import TagWidget

from assessments.constants import AnswerChoices, InfoValueLevels, RiskLevels
from assessments.models import Assessment

from .constants import AnswerChoices, InfoValueChoices, RiskLevels
from .models import Answer, Assessment, Question, Questionnaire


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "help_text", "is_required", "is_archived"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "help_text": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ["name", "description", "tags", "is_archived"]
        widgets = {
            "tags": TagWidget(),
        }


class AssessmentForm(forms.ModelForm):
    info_value = forms.ChoiceField(
        choices=InfoValueLevels.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
        help_text="How sensitive is the data handled by this vendor?",
    )
    risk_level = forms.ChoiceField(
        choices=RiskLevels.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
        help_text="Overall risk level of this assessment.",
    )

    class Meta:
        model = Assessment
        fields = ["questionnaire", "information_value", "risk_level", "status"]
        widgets = {
            "information_value": forms.Select(choices=InfoValueChoices.choices),
            "risk_level": forms.Select(choices=RiskLevels.choices),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["response", "supporting_text", "comments", "evidence"]
        widgets = {
            "response": forms.Select(choices=AnswerChoices.choices),
        }
        labels = {
            "response": "Answer",
            "supporting_text": "Explain your response (optional)",
            "evidence": "Attach file (if any)",
        }


class InlineAnswerForm(forms.ModelForm):
    """Optional: Used for displaying answers inline with questions (e.g., in HTMX forms)
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
