from django.http import JsonResponse
from django.shortcuts import redirect, render


def home(request):
    """Redirect root URL to the dashboard."""
    return redirect("sessions:dashboard")


def health(request):
    return JsonResponse({"status": "ok"})


def handler404(request, exception):
    """Custom 404 page."""
    return render(request, "404.html", status=404)


def handler500(request):
    """Custom 500 page."""
    return render(request, "500.html", status=500)
