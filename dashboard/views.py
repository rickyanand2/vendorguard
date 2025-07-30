# dashboard/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.http import JsonResponse
from django.views.generic import TemplateView, View

from assessments.models import Assessment
from vendors.models import Vendor


# Main dashboard page view – loads the HTML template
class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"


# JSON API view to return stats for frontend JavaScript
class DashboardStatsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        org = request.user.organization
        if not org:
            return JsonResponse({"error": "Organization not found."}, status=403)

        # Filter data to current user's organization
        vendors = Vendor.objects.filter(organization=org)
        total_vendors = vendors.count()
        total_offerings = sum(v.offerings.count() for v in vendors)

        assessments = Assessment.objects.filter(status="completed", organization=org)
        total_assessments = assessments.count()

        avg_score = vendors.aggregate(avg=Avg("trust_profile__trust_score"))["avg"] or 0
        high_risk = vendors.filter(trust_profile__trust_score__lt=400).count()

        return JsonResponse(
            {
                "total_vendors": total_vendors,
                "total_offerings": total_offerings,
                "total_assessments": total_assessments,
                "average_score": round(avg_score, 1),
                "high_risk_vendors": high_risk,
            }
        )
