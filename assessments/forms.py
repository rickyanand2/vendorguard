from django import forms
from assessments.models import Assessment
from taggit.forms import TagField
from assessments.constants import InfoValueLevels, RiskLevels
from .models import Answer, Assessment, Questionnaire, Question
from assessments.constants import ANSWER_CHOICES


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
        fields = ["questionnaire", "vendor_offering", "info_value", "risk_level"]


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["answer", "response", "comments"]
        widgets = {
            "response": forms.Select(
                choices=ANSWER_CHOICES, attrs={"class": "form-select"}
            )
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
