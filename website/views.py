from django.shortcuts import render


# ================================
# 🏠 Home View (Public)
# ================================
def home(request):
    return render(request, "website/home.html")
