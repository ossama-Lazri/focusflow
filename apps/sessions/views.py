"""
Views for the FocusFlow sessions app.
All HTMX interactions return partials; normal requests return full pages.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from .models import FocusSession
from . import services


def dashboard(request):
    """Main dashboard: active session, quick-create, recent sessions, today's stats."""
    active_session = FocusSession.objects.filter(
        status=FocusSession.STATUS_ACTIVE
    ).first()
    recent_sessions = FocusSession.objects.all()[:5]
    daily_stats = services.get_daily_stats()

    context = {
        "active_session": active_session,
        "recent_sessions": recent_sessions,
        "daily_stats": daily_stats,
        "page_title": "Dashboard",
        "greeting": _get_greeting(),
        "today": timezone.now(),
    }
    return render(request, "sessions/dashboard.html", context)


def session_history(request):
    """Full paginated session history."""
    session_list = FocusSession.objects.all()
    paginator = Paginator(session_list, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "sessions": page_obj.object_list,
        "page_title": "History",
    }
    return render(request, "sessions/history.html", context)


def statistics(request):
    """Daily and weekly statistics."""
    daily_stats = services.get_daily_stats()
    weekly_stats = services.get_weekly_stats()

    context = {
        "daily_stats": daily_stats,
        "weekly_stats": weekly_stats,
        "page_title": "Statistics",
    }
    return render(request, "sessions/stats.html", context)


@require_http_methods(["POST"])
def create_session(request):
    """Create a new focus session. Returns a session row partial (HTMX) or redirects."""
    label = request.POST.get("label", "").strip()

    if not label:
        if request.htmx:
            return HttpResponse(
                '<div class="toast toast--error" x-data="{show:true}" x-show="show" '
                'x-init="setTimeout(()=>show=false,3000)">Label cannot be empty.</div>',
                status=422,
            )
        messages.error(request, "Session label cannot be empty.")
        return redirect("sessions:dashboard")

    session = services.create_session(label)

    if request.htmx:
        response = HttpResponse()
        response["HX-Redirect"] = "/dashboard/"
        return response

    messages.success(request, f'Session "{label}" created.')
    return redirect("sessions:dashboard")


@require_http_methods(["POST"])
def start_session(request, pk):
    """Start a focus session."""
    session = get_object_or_404(FocusSession, pk=pk)
    session = services.start_session(session)

    if request.htmx:
        # Return updated row + trigger dashboard refresh
        response = render(
            request, "sessions/partials/_session_row.html", {"session": session}
        )
        response["HX-Trigger"] = "sessionStarted"
        return response

    return redirect("sessions:dashboard")


@require_http_methods(["POST"])
def stop_session(request, pk):
    """Stop an active focus session."""
    session = get_object_or_404(FocusSession, pk=pk)
    session = services.stop_session(session)

    if request.htmx:
        response = render(
            request, "sessions/partials/_session_row.html", {"session": session}
        )
        response["HX-Trigger"] = "sessionStopped"
        return response

    return redirect("sessions:dashboard")


@require_http_methods(["POST", "DELETE"])
def delete_session(request, pk):
    """Delete a focus session."""
    session = get_object_or_404(FocusSession, pk=pk)
    session.delete()

    if request.htmx:
        response = HttpResponse("")
        response["HX-Trigger"] = "sessionDeleted"
        return response

    messages.success(request, "Session deleted.")
    return redirect("sessions:dashboard")


def session_timer(request, pk):
    """
    Return just the timer partial for live polling via HTMX.
    Called every 1 second by the active timer display.
    """
    session = get_object_or_404(FocusSession, pk=pk)
    return render(
        request, "sessions/partials/_session_timer.html", {"session": session}
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_greeting() -> str:
    hour = timezone.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"
