import time
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from apps.sessions.models import FocusSession

_START_TIME = time.time()


def home(request):
    """Redirect root URL to the dashboard."""
    return redirect("sessions:dashboard")


def health(request):
    return JsonResponse({"status": "ok"})


def metrics(request):
    """Prometheus exposition metrics endpoint."""
    total_sessions = FocusSession.objects.count()
    active_sessions = FocusSession.objects.filter(
        status=FocusSession.STATUS_ACTIVE
    ).count()
    completed_sessions = FocusSession.objects.filter(
        status=FocusSession.STATUS_COMPLETED
    ).count()
    total_focus_seconds = (
        FocusSession.objects.filter(status=FocusSession.STATUS_COMPLETED).aggregate(
            Sum("duration_seconds")
        )["duration_seconds__sum"]
        or 0
    )
    uptime_seconds = time.time() - _START_TIME

    output = (
        "# HELP focusflow_up Application availability status\n"
        "# TYPE focusflow_up gauge\n"
        "focusflow_up 1\n"
        "# HELP focusflow_uptime_seconds Application uptime in seconds\n"
        "# TYPE focusflow_uptime_seconds counter\n"
        f"focusflow_uptime_seconds {uptime_seconds:.2f}\n"
        "# HELP focusflow_sessions_total Total focus sessions count\n"
        "# TYPE focusflow_sessions_total gauge\n"
        f"focusflow_sessions_total {total_sessions}\n"
        "# HELP focusflow_sessions_active Currently active focus sessions\n"
        "# TYPE focusflow_sessions_active gauge\n"
        f"focusflow_sessions_active {active_sessions}\n"
        "# HELP focusflow_sessions_completed Total completed focus sessions\n"
        "# TYPE focusflow_sessions_completed gauge\n"
        f"focusflow_sessions_completed {completed_sessions}\n"
        "# HELP focusflow_focus_time_seconds_total Total cumulative focus seconds\n"
        "# TYPE focusflow_focus_time_seconds_total counter\n"
        f"focusflow_focus_time_seconds_total {total_focus_seconds}\n"
    )
    return HttpResponse(output, content_type="text/plain; version=0.0.4; charset=utf-8")


def handler404(request, exception):
    """Custom 404 page."""
    return render(request, "404.html", status=404)


def handler500(request):
    """Custom 500 page."""
    return render(request, "500.html", status=500)
