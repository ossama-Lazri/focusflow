import pytest
from django.urls import reverse
from apps.sessions.models import FocusSession

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDashboardView:
    def test_get_returns_200(self, client):
        response = client.get(reverse("sessions:dashboard"))
        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        response = client.get(reverse("sessions:dashboard"))
        assert "sessions/dashboard.html" in [t.name for t in response.templates]

    def test_context_has_daily_stats(self, client):
        response = client.get(reverse("sessions:dashboard"))
        assert "daily_stats" in response.context

    def test_context_has_recent_sessions(self, client):
        response = client.get(reverse("sessions:dashboard"))
        assert "recent_sessions" in response.context

    def test_context_has_greeting(self, client):
        response = client.get(reverse("sessions:dashboard"))
        assert "greeting" in response.context
        assert response.context["greeting"] in (
            "Good morning",
            "Good afternoon",
            "Good evening",
        )

    def test_recent_sessions_limited_to_five(self, client, db):
        for i in range(8):
            FocusSession.objects.create(label=f"Session {i}")
        response = client.get(reverse("sessions:dashboard"))
        assert len(response.context["recent_sessions"]) == 5

    def test_active_session_in_context(self, client, active_session):
        response = client.get(reverse("sessions:dashboard"))
        assert response.context["active_session"] == active_session

    def test_no_active_session_returns_none(self, client, db):
        response = client.get(reverse("sessions:dashboard"))
        assert response.context["active_session"] is None

    def test_contains_new_session_button(self, client):
        response = client.get(reverse("sessions:dashboard"))
        assert b"New Session" in response.content

    def test_shows_empty_state_with_no_sessions(self, client, db):
        response = client.get(reverse("sessions:dashboard"))
        assert b"No sessions yet" in response.content


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSessionHistoryView:
    def test_get_returns_200(self, client):
        response = client.get(reverse("sessions:history"))
        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        response = client.get(reverse("sessions:history"))
        assert "sessions/history.html" in [t.name for t in response.templates]

    def test_context_has_sessions(self, client):
        response = client.get(reverse("sessions:history"))
        assert "sessions" in response.context

    def test_context_has_page_obj(self, client):
        response = client.get(reverse("sessions:history"))
        assert "page_obj" in response.context

    def test_paginates_at_20(self, client, db):
        for i in range(25):
            FocusSession.objects.create(label=f"Session {i}")
        response = client.get(reverse("sessions:history"))
        assert len(response.context["sessions"]) == 20

    def test_second_page_accessible(self, client, db):
        for i in range(25):
            FocusSession.objects.create(label=f"Session {i}")
        response = client.get(reverse("sessions:history") + "?page=2")
        assert response.status_code == 200
        assert len(response.context["sessions"]) == 5

    def test_shows_empty_state_with_no_sessions(self, client, db):
        response = client.get(reverse("sessions:history"))
        assert b"No sessions yet" in response.content

    def test_shows_session_labels(self, client, db):
        FocusSession.objects.create(label="Deep focus block")
        response = client.get(reverse("sessions:history"))
        assert b"Deep focus block" in response.content


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStatisticsView:
    def test_get_returns_200(self, client):
        response = client.get(reverse("sessions:statistics"))
        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        response = client.get(reverse("sessions:statistics"))
        assert "sessions/stats.html" in [t.name for t in response.templates]

    def test_context_has_daily_stats(self, client):
        response = client.get(reverse("sessions:statistics"))
        assert "daily_stats" in response.context

    def test_context_has_weekly_stats(self, client):
        response = client.get(reverse("sessions:statistics"))
        assert "weekly_stats" in response.context

    def test_weekly_stats_has_seven_days(self, client):
        response = client.get(reverse("sessions:statistics"))
        assert len(response.context["weekly_stats"]["days"]) == 7

    def test_contains_bar_chart(self, client):
        response = client.get(reverse("sessions:statistics"))
        assert b"bar-chart" in response.content


# ---------------------------------------------------------------------------
# Create Session
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateSessionView:
    def test_post_with_label_creates_session(self, client):
        client.post(reverse("sessions:create_session"), {"label": "New session"})
        assert FocusSession.objects.filter(label="New session").exists()

    def test_post_redirects_to_dashboard(self, client):
        response = client.post(reverse("sessions:create_session"), {"label": "Test"})
        assert response.status_code == 302
        assert response["Location"] == reverse("sessions:dashboard")

    def test_get_not_allowed(self, client):
        response = client.get(reverse("sessions:create_session"))
        assert response.status_code == 405

    def test_empty_label_redirects_without_creating(self, client):
        response = client.post(reverse("sessions:create_session"), {"label": ""})
        assert response.status_code == 302
        assert FocusSession.objects.count() == 0

    def test_whitespace_only_label_rejected(self, client):
        client.post(reverse("sessions:create_session"), {"label": "   "})
        assert FocusSession.objects.count() == 0

    def test_htmx_empty_label_returns_422(self, client, htmx_headers):
        response = client.post(
            reverse("sessions:create_session"),
            {"label": ""},
            **htmx_headers,
        )
        assert response.status_code == 422

    def test_htmx_success_returns_hx_redirect(self, client, htmx_headers):
        response = client.post(
            reverse("sessions:create_session"),
            {"label": "HTMX session"},
            **htmx_headers,
        )
        assert response.status_code == 200
        assert "HX-Redirect" in response
        assert response["HX-Redirect"] == "/dashboard/"

    def test_htmx_success_still_creates_session(self, client, htmx_headers):
        client.post(
            reverse("sessions:create_session"),
            {"label": "HTMX session"},
            **htmx_headers,
        )
        assert FocusSession.objects.filter(label="HTMX session").exists()

    def test_label_stripped_of_whitespace(self, client):
        client.post(reverse("sessions:create_session"), {"label": "  Trimmed  "})
        assert FocusSession.objects.filter(label="Trimmed").exists()


# ---------------------------------------------------------------------------
# Start Session
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStartSessionView:
    def test_post_starts_session(self, client, idle_session):
        client.post(reverse("sessions:start_session", args=[idle_session.pk]))
        idle_session.refresh_from_db()
        assert idle_session.status == FocusSession.STATUS_ACTIVE

    def test_post_redirects_to_dashboard(self, client, idle_session):
        response = client.post(
            reverse("sessions:start_session", args=[idle_session.pk])
        )
        assert response.status_code == 302
        assert response["Location"] == reverse("sessions:dashboard")

    def test_get_not_allowed(self, client, idle_session):
        response = client.get(reverse("sessions:start_session", args=[idle_session.pk]))
        assert response.status_code == 405

    def test_invalid_pk_returns_404(self, client):
        response = client.post(reverse("sessions:start_session", args=[99999]))
        assert response.status_code == 404

    def test_htmx_returns_session_row_partial(self, client, idle_session, htmx_headers):
        response = client.post(
            reverse("sessions:start_session", args=[idle_session.pk]),
            **htmx_headers,
        )
        assert response.status_code == 200
        assert b"session-row" in response.content

    def test_htmx_response_has_hx_trigger(self, client, idle_session, htmx_headers):
        response = client.post(
            reverse("sessions:start_session", args=[idle_session.pk]),
            **htmx_headers,
        )
        assert response["HX-Trigger"] == "sessionStarted"

    def test_htmx_response_shows_active_badge(self, client, idle_session, htmx_headers):
        response = client.post(
            reverse("sessions:start_session", args=[idle_session.pk]),
            **htmx_headers,
        )
        assert b"Active" in response.content


# ---------------------------------------------------------------------------
# Stop Session
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStopSessionView:
    def test_post_stops_session(self, client, active_session):
        client.post(reverse("sessions:stop_session", args=[active_session.pk]))
        active_session.refresh_from_db()
        assert active_session.status == FocusSession.STATUS_COMPLETED

    def test_post_redirects_to_dashboard(self, client, active_session):
        response = client.post(
            reverse("sessions:stop_session", args=[active_session.pk])
        )
        assert response.status_code == 302
        assert response["Location"] == reverse("sessions:dashboard")

    def test_get_not_allowed(self, client, active_session):
        response = client.get(
            reverse("sessions:stop_session", args=[active_session.pk])
        )
        assert response.status_code == 405

    def test_invalid_pk_returns_404(self, client):
        response = client.post(reverse("sessions:stop_session", args=[99999]))
        assert response.status_code == 404

    def test_htmx_returns_session_row_partial(
        self, client, active_session, htmx_headers
    ):
        response = client.post(
            reverse("sessions:stop_session", args=[active_session.pk]),
            **htmx_headers,
        )
        assert response.status_code == 200
        assert b"session-row" in response.content

    def test_htmx_response_has_hx_trigger(self, client, active_session, htmx_headers):
        response = client.post(
            reverse("sessions:stop_session", args=[active_session.pk]),
            **htmx_headers,
        )
        assert response["HX-Trigger"] == "sessionStopped"

    def test_htmx_response_shows_completed_badge(
        self, client, active_session, htmx_headers
    ):
        response = client.post(
            reverse("sessions:stop_session", args=[active_session.pk]),
            **htmx_headers,
        )
        assert b"Completed" in response.content

    def test_records_duration(self, client, active_session):
        client.post(reverse("sessions:stop_session", args=[active_session.pk]))
        active_session.refresh_from_db()
        assert active_session.duration_seconds > 0


# ---------------------------------------------------------------------------
# Delete Session
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDeleteSessionView:
    def test_post_deletes_session(self, client, idle_session):
        pk = idle_session.pk
        client.post(reverse("sessions:delete_session", args=[pk]))
        assert not FocusSession.objects.filter(pk=pk).exists()

    def test_post_redirects_to_dashboard(self, client, idle_session):
        response = client.post(
            reverse("sessions:delete_session", args=[idle_session.pk])
        )
        assert response.status_code == 302
        assert response["Location"] == reverse("sessions:dashboard")

    def test_get_not_allowed(self, client, idle_session):
        response = client.get(
            reverse("sessions:delete_session", args=[idle_session.pk])
        )
        assert response.status_code == 405

    def test_invalid_pk_returns_404(self, client):
        response = client.post(reverse("sessions:delete_session", args=[99999]))
        assert response.status_code == 404

    def test_htmx_returns_empty_200(self, client, idle_session, htmx_headers):
        response = client.post(
            reverse("sessions:delete_session", args=[idle_session.pk]),
            **htmx_headers,
        )
        assert response.status_code == 200
        assert response.content == b""

    def test_htmx_response_has_hx_trigger(self, client, idle_session, htmx_headers):
        response = client.post(
            reverse("sessions:delete_session", args=[idle_session.pk]),
            **htmx_headers,
        )
        assert response["HX-Trigger"] == "sessionDeleted"

    def test_can_delete_active_session(self, client, active_session):
        pk = active_session.pk
        client.post(reverse("sessions:delete_session", args=[pk]))
        assert not FocusSession.objects.filter(pk=pk).exists()

    def test_can_delete_completed_session(self, client, completed_session):
        pk = completed_session.pk
        client.post(reverse("sessions:delete_session", args=[pk]))
        assert not FocusSession.objects.filter(pk=pk).exists()


# ---------------------------------------------------------------------------
# Session Timer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSessionTimerView:
    def test_get_returns_200(self, client, active_session):
        response = client.get(
            reverse("sessions:session_timer", args=[active_session.pk])
        )
        assert response.status_code == 200

    def test_uses_timer_partial_template(self, client, active_session):
        response = client.get(
            reverse("sessions:session_timer", args=[active_session.pk])
        )
        assert "sessions/partials/_session_timer.html" in [
            t.name for t in response.templates
        ]

    def test_invalid_pk_returns_404(self, client):
        response = client.get(reverse("sessions:session_timer", args=[99999]))
        assert response.status_code == 404

    def test_contains_elapsed_time(self, client, active_session):
        response = client.get(
            reverse("sessions:session_timer", args=[active_session.pk])
        )
        assert b"timer-display" in response.content

    def test_idle_session_renders_empty(self, client, idle_session):
        response = client.get(reverse("sessions:session_timer", args=[idle_session.pk]))
        assert response.status_code == 200
        assert b"active-panel" not in response.content


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRootRedirect:
    def test_root_redirects_to_dashboard(self, client):
        response = client.get("/")
        assert response.status_code == 302
        assert "/dashboard/" in response["Location"]


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUtilityEndpoints:
    def test_favicon_returns_204(self, client):
        response = client.get("/favicon.ico")
        assert response.status_code == 204

    def test_chrome_devtools_returns_404_outside_debug(self, client):
        response = client.get("/.well-known/appspecific/com.chrome.devtools.json")
        assert response.status_code == 404
