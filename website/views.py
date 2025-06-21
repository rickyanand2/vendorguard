from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# ================================
# 🏠 Home View (Public or After Login)
# ================================
def home(request):
    return render(request, "website/home.html")
