# assessments/admin.py

from django.contrib import admin
from .models import (
    Assessment,
    Questionnaire,
    Question,
    Answer,
    Certification,
    QuestionnaireQuestion,
)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_questionnaire_name",
        "vendor_offering",
        "status",
        "information_value",
        "recommended_score",
        "risk_level",
        "created_at",
    )
    list_filter = ("status", "risk_level", "information_value", "created_at")
    search_fields = ("vendor_offering__name", "questionnaire__name")

    def get_questionnaire_name(self, obj):
        return obj.questionnaire.name

    get_questionnaire_name.short_description = "Questionnaire"


class QuestionnaireQuestionInline(admin.TabularInline):
    model = QuestionnaireQuestion
    extra = 1
    autocomplete_fields = ["questionnaire"]
    ordering = ["order"]


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "is_archived", "created_at")
    inlines = [QuestionnaireQuestionInline]
    search_fields = ("name", "description")
    list_filter = ("is_archived",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "text",
        "questionnaire",
        "category",
        "response_type",
        "weight",
        "is_archived",
    )
    list_filter = ("questionnaire", "category", "is_archived")
    search_fields = ("text", "help_text")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "assessment", "question", "answer", "risk_impact")
    search_fields = ("assessment__vendor_offering__name", "question__text")


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor",
        "type",
        "is_valid",
        "issued_date",
        "expiry_date",
        "is_archived",
    )
    list_filter = ("type", "is_valid", "is_archived")
    search_fields = ("vendor__name", "cert_number")
