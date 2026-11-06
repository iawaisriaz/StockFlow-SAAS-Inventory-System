from django.shortcuts import render, redirect


def landing(request):

    # Already logged-in user → Dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")

    # Guest user → Landing Page
    return render(request, "core/landing.html")