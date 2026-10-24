import pytest
from datetime import timedelta
from django.utils import timezone
from apps.sessions.models import FocusSession
from apps.sessions import services


@pytest.mark.django_db
class TestDailyStatsFormatting:
    """Exhaustive formatting branch coverage for get_daily_stats."""

    def _make_completed(self, duration_seconds):
        now = timezone.now()
        return FocusSession.objects.create(
            label="T",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=duration_seconds,
            started_at=now,
            stopped_at=now,
        )

    def test_zero_seconds_formatted(self):
        self._make_completed(0)
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "0s"

    def test_59_seconds_formatted(self):
        self._make_completed(59)
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "59s"

    def test_60_seconds_formatted_as_minutes(self):
        self._make_completed(60)
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "1m"

    def test_3599_seconds_formatted_as_minutes(self):
        self._make_completed(3599)
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "59m"

    def test_3600_seconds_formatted_as_hours(self):
        self._make_completed(3600)
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "1h 0m"

    def test_3660_seconds_formatted_as_hours_and_minutes(self):
        self._make_completed(3660)
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "1h 1m"

    def test_multiple_completed_sessions_summed(self):
        for _ in range(3):
            self._make_completed(600)
        stats = services.get_daily_stats()
        assert stats["total_seconds"] == 1800
        assert stats["session_count"] == 3

    def test_active_sessions_not_in_session_count(self):
        FocusSession.objects.create(
            label="Running",
            status=FocusSession.STATUS_ACTIVE,
            started_at=timezone.now(),
        )
        stats = services.get_daily_stats()
        assert stats["session_count"] == 0
        assert stats["active_count"] == 1

    def test_idle_sessions_ignored_in_all_counts(self):
        FocusSession.objects.create(label="Idle")
        stats = services.get_daily_stats()
        assert stats["session_count"] == 0
        assert stats["active_count"] == 0
        assert stats["total_seconds"] == 0


@pytest.mark.django_db
class TestWeeklyStatsFormatting:
    """Exhaustive formatting and edge-case coverage for get_weekly_stats."""

    def _make_completed_today(self, duration_seconds):
        now = timezone.now()
        return FocusSession.objects.create(
            label="T",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=duration_seconds,
            started_at=now,
            stopped_at=now,
        )

    def test_week_total_formatted_minutes_only(self):
        self._make_completed_today(1800)
        stats = services.get_weekly_stats()
        assert stats["total_formatted"] == "30m"

    def test_week_total_formatted_hours_and_minutes(self):
        self._make_completed_today(5400)
        stats = services.get_weekly_stats()
        assert stats["total_formatted"] == "1h 30m"

    def test_week_total_formatted_zero_minutes(self):
        self._make_completed_today(3600)
        stats = services.get_weekly_stats()
        assert stats["total_formatted"] == "1h 0m"

    def test_days_chronological_order(self):
        stats = services.get_weekly_stats()
        dates = [d["date"] for d in stats["days"]]
        assert dates == sorted(dates)

    def test_bar_pct_capped_at_100(self):
        self._make_completed_today(7200)
        stats = services.get_weekly_stats()
        for day in stats["days"]:
            assert day["bar_pct"] <= 100.0

    def test_bar_pct_non_negative(self):
        stats = services.get_weekly_stats()
        for day in stats["days"]:
            assert day["bar_pct"] >= 0

    def test_max_seconds_reflects_busiest_day(self):
        self._make_completed_today(9000)
        stats = services.get_weekly_stats()
        assert stats["max_seconds"] == 9000

    def test_multiple_sessions_same_day_aggregated(self):
        for _ in range(4):
            self._make_completed_today(900)
        stats = services.get_weekly_stats()
        today = next(d for d in stats["days"] if d["is_today"])
        assert today["session_count"] == 4
        assert today["total_seconds"] == 3600

    def test_idle_and_active_excluded_from_weekly(self):
        now = timezone.now()
        FocusSession.objects.create(label="Idle")
        FocusSession.objects.create(
            label="Running",
            status=FocusSession.STATUS_ACTIVE,
            started_at=now,
        )
        stats = services.get_weekly_stats()
        assert stats["total_sessions"] == 0
        assert stats["total_seconds"] == 0


@pytest.mark.django_db
class TestServiceIntegration:
    """Full workflow integration: create → start → stop → stats."""

    def test_full_session_lifecycle_reflected_in_daily_stats(self):
        session = services.create_session("Integration test")
        assert services.get_daily_stats()["session_count"] == 0

        services.start_session(session)
        assert services.get_daily_stats()["active_count"] == 1

        # push started_at back so stop_session records a non-zero duration
        FocusSession.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(seconds=5)
        )
        session.refresh_from_db()
        services.stop_session(session)

        stats = services.get_daily_stats()
        assert stats["session_count"] == 1
        assert stats["active_count"] == 0
        assert stats["total_seconds"] > 0

    def test_full_session_lifecycle_reflected_in_weekly_stats(self):
        session = services.create_session("Weekly test")
        services.start_session(session)

        FocusSession.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(seconds=5)
        )
        session.refresh_from_db()
        services.stop_session(session)

        stats = services.get_weekly_stats()
        assert stats["total_sessions"] == 1
        assert stats["total_seconds"] > 0

    def test_starting_second_session_stops_first(self):
        s1 = services.create_session("First")
        s2 = services.create_session("Second")

        services.start_session(s1)
        services.start_session(s2)

        s1.refresh_from_db()
        s2.refresh_from_db()

        assert s1.status == FocusSession.STATUS_COMPLETED
        assert s2.status == FocusSession.STATUS_ACTIVE
        assert (
            FocusSession.objects.filter(status=FocusSession.STATUS_ACTIVE).count() == 1
        )

    def test_stop_records_accurate_duration(self):
        session = services.create_session("Timed")
        services.start_session(session)
        services.stop_session(session)

        session.refresh_from_db()
        assert session.duration_seconds >= 0
        assert session.stopped_at is not None
        assert session.started_at is not None
        assert session.stopped_at >= session.started_at
