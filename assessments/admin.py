# assessments/admin.py

from django.contrib import admin
from .models import Questionnaire, Question, Assessment, Answer


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "questionnaire", "weight")
    search_fields = ("text", "help_text")
    list_filter = ("questionnaire",)
    ordering = ("questionnaire", "weight")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    # Safe accessor for vendor via VendorOffering
    def get_vendor(self, obj):
        return obj.VendorOffering.vendor

    get_vendor.short_description = "Vendor"
    get_vendor.admin_order_field = "vendor_offering__vendor"

    list_display = (
        "name",
        "description",
        "get_vendor",
        "vendor_offering",
        "organization",
        "questionnaire",
        "status",
        "risk_level",
        "created_at",
    )

    search_fields = (
        "name",
        "VendorOffering__vendor__name",
        "organization__name",
        "questionnaire__name",
    )
    filter_horizontal = ("tags",)
    list_filter = ("status", "questionnaire", "created_at")
    ordering = ("-created_at",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("assessment", "question", "answer", "risk_impact")
    search_fields = ("question__text", "assessment__VendorOffering__vendor__name")
    list_filter = ("answer", "question__questionnaire")
