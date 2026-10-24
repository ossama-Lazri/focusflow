"""
Business logic services for FocusSession operations.
All database mutations go through here — views stay thin.
"""

from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import FocusSession


def create_session(label: str) -> FocusSession:
    """Create a new idle focus session with the given label."""
    session = FocusSession.objects.create(label=label.strip())
    return session


def start_session(session: FocusSession) -> FocusSession:
    """
    Start a focus session.
    Only idle sessions can be started.
    Any currently active session is stopped first.
    """
    # Stop any currently active sessions
    active_sessions = FocusSession.objects.filter(status=FocusSession.STATUS_ACTIVE)
    for active in active_sessions:
        stop_session(active)

    session.status = FocusSession.STATUS_ACTIVE
    session.started_at = timezone.now()
    session.save(update_fields=["status", "started_at", "updated_at"])
    return session


def stop_session(session: FocusSession) -> FocusSession:
    """
    Stop an active focus session and record the total duration.
    """
    if session.status != FocusSession.STATUS_ACTIVE:
        return session

    now = timezone.now()
    session.stopped_at = now

    if session.started_at:
        elapsed = (now - session.started_at).total_seconds()
        session.duration_seconds = int(elapsed)
    else:
        session.duration_seconds = 0

    session.status = FocusSession.STATUS_COMPLETED
    session.save(
        update_fields=["status", "stopped_at", "duration_seconds", "updated_at"]
    )
    return session


def get_daily_stats(target_date=None) -> dict:
    """
    Return statistics for a single day.
    Defaults to today (UTC).
    """
    if target_date is None:
        target_date = timezone.now().date()

    sessions = FocusSession.objects.filter(created_at__date=target_date)

    completed = sessions.filter(status=FocusSession.STATUS_COMPLETED)
    total_seconds = completed.aggregate(total=Sum("duration_seconds"))["total"] or 0
    session_count = completed.count()
    active_count = sessions.filter(status=FocusSession.STATUS_ACTIVE).count()

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours:
        total_formatted = f"{hours}h {minutes}m"
    elif minutes:
        total_formatted = f"{minutes}m"
    else:
        total_formatted = f"{total_seconds}s"

    return {
        "date": target_date,
        "session_count": session_count,
        "active_count": active_count,
        "total_seconds": total_seconds,
        "total_formatted": total_formatted,
        "sessions": sessions,
    }


def get_weekly_stats() -> dict:
    """
    Return per-day stats for the last 7 days (most recent last).
    """
    today = timezone.now().date()
    days = []
    max_seconds = 0

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        completed = FocusSession.objects.filter(
            created_at__date=day,
            status=FocusSession.STATUS_COMPLETED,
        )
        total_seconds = completed.aggregate(total=Sum("duration_seconds"))["total"] or 0
        session_count = completed.count()

        if total_seconds > max_seconds:
            max_seconds = total_seconds

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours:
            label = f"{hours}h {minutes}m"
        elif minutes:
            label = f"{minutes}m"
        else:
            label = f"{total_seconds}s" if total_seconds else "—"

        days.append(
            {
                "date": day,
                "day_name": day.strftime("%a"),
                "day_label": day.strftime("%b %d").replace(" 0", " "),
                "total_seconds": total_seconds,
                "total_formatted": label,
                "session_count": session_count,
                "is_today": day == today,
            }
        )

    # Calculate bar heights (percentage of max)
    for day in days:
        if max_seconds > 0:
            day["bar_pct"] = round((day["total_seconds"] / max_seconds) * 100, 1)
        else:
            day["bar_pct"] = 0

    total_week_seconds = sum(d["total_seconds"] for d in days)
    week_hours = total_week_seconds // 3600
    week_minutes = (total_week_seconds % 3600) // 60

    return {
        "days": days,
        "max_seconds": max_seconds,
        "total_seconds": total_week_seconds,
        "total_formatted": (
            f"{week_hours}h {week_minutes}m" if week_hours else f"{week_minutes}m"
        ),
        "total_sessions": sum(d["session_count"] for d in days),
    }
