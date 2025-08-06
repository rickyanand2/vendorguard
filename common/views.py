# common/views.py

from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import TestForm


class CommonTestLayoutView(FormView):
    """Test form used for test_layout.html."""

    template_name = "common/test_layout.html"
    form_class = TestForm
    success_url = reverse_lazy("common:test_layout")  # or your actual URL name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alert_tags"] = [
            "success",
            "warning",
            "danger",
            "info",
        ]  # Bootstrap uses 'danger', not 'error'
        return context

    def form_valid(self, form):
        # Add success logic here, e.g., messages
        return super().form_valid(form)
