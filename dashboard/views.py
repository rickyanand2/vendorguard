from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def user_dashboard(request):
    return render(request, "dashboard/dashboard.html")
