import pytest
from datetime import timedelta
from django.utils import timezone
from apps.sessions.models import FocusSession
from apps.sessions import services


@pytest.mark.django_db
class TestCreateSession:
    def test_creates_with_correct_label(self):
        session = services.create_session("Deep work")
        assert session.label == "Deep work"

    def test_strips_whitespace_from_label(self):
        session = services.create_session("  API design  ")
        assert session.label == "API design"

    def test_default_status_is_idle(self):
        session = services.create_session("Test")
        assert session.status == FocusSession.STATUS_IDLE

    def test_returns_focus_session_instance(self):
        session = services.create_session("Test")
        assert isinstance(session, FocusSession)

    def test_session_persisted_to_db(self):
        services.create_session("Persisted")
        assert FocusSession.objects.filter(label="Persisted").exists()


@pytest.mark.django_db
class TestStartSession:
    def test_sets_status_to_active(self, idle_session):
        session = services.start_session(idle_session)
        assert session.status == FocusSession.STATUS_ACTIVE

    def test_sets_started_at(self, idle_session):
        before = timezone.now()
        session = services.start_session(idle_session)
        assert session.started_at >= before

    def test_persists_changes(self, idle_session):
        services.start_session(idle_session)
        refreshed = FocusSession.objects.get(pk=idle_session.pk)
        assert refreshed.status == FocusSession.STATUS_ACTIVE

    def test_returns_focus_session_instance(self, idle_session):
        result = services.start_session(idle_session)
        assert isinstance(result, FocusSession)

    def test_stops_existing_active_session(self, db):
        running = services.create_session("Already running")
        services.start_session(running)

        new_session = services.create_session("New session")
        services.start_session(new_session)

        running.refresh_from_db()
        assert running.status == FocusSession.STATUS_COMPLETED

    def test_only_one_active_session_at_a_time(self, db):
        s1 = services.create_session("S1")
        s2 = services.create_session("S2")
        services.start_session(s1)
        services.start_session(s2)

        active = FocusSession.objects.filter(status=FocusSession.STATUS_ACTIVE)
        assert active.count() == 1
        assert active.first().pk == s2.pk


@pytest.mark.django_db
class TestStopSession:
    def test_sets_status_to_completed(self, active_session):
        session = services.stop_session(active_session)
        assert session.status == FocusSession.STATUS_COMPLETED

    def test_sets_stopped_at(self, active_session):
        before = timezone.now()
        session = services.stop_session(active_session)
        assert session.stopped_at >= before

    def test_calculates_duration_seconds(self, active_session):
        session = services.stop_session(active_session)
        assert session.duration_seconds >= 1800
        assert session.duration_seconds < 1860

    def test_persists_changes(self, active_session):
        services.stop_session(active_session)
        refreshed = FocusSession.objects.get(pk=active_session.pk)
        assert refreshed.status == FocusSession.STATUS_COMPLETED
        assert refreshed.duration_seconds > 0

    def test_noop_on_idle_session(self, idle_session):
        result = services.stop_session(idle_session)
        assert result.status == FocusSession.STATUS_IDLE

    def test_noop_on_completed_session(self, completed_session):
        original_duration = completed_session.duration_seconds
        result = services.stop_session(completed_session)
        assert result.status == FocusSession.STATUS_COMPLETED
        assert result.duration_seconds == original_duration

    def test_duration_zero_when_no_started_at(self, db):
        session = FocusSession.objects.create(
            label="No start",
            status=FocusSession.STATUS_ACTIVE,
            started_at=None,
        )
        result = services.stop_session(session)
        assert result.duration_seconds == 0

    def test_returns_focus_session_instance(self, active_session):
        result = services.stop_session(active_session)
        assert isinstance(result, FocusSession)


@pytest.mark.django_db
class TestGetDailyStats:
    def test_empty_db_returns_zero_counts(self):
        stats = services.get_daily_stats()
        assert stats["session_count"] == 0
        assert stats["active_count"] == 0
        assert stats["total_seconds"] == 0

    def test_returns_correct_date(self):
        today = timezone.now().date()
        stats = services.get_daily_stats()
        assert stats["date"] == today

    def test_accepts_custom_date(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        stats = services.get_daily_stats(target_date=yesterday)
        assert stats["date"] == yesterday

    def test_counts_completed_sessions(self, completed_session):
        stats = services.get_daily_stats()
        assert stats["session_count"] == 1

    def test_counts_active_sessions(self, active_session):
        stats = services.get_daily_stats()
        assert stats["active_count"] == 1

    def test_idle_not_counted_in_session_count(self, idle_session):
        stats = services.get_daily_stats()
        assert stats["session_count"] == 0

    def test_sums_duration_seconds(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="A",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=1800,
            started_at=now,
            stopped_at=now,
        )
        FocusSession.objects.create(
            label="B",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=3600,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_daily_stats()
        assert stats["total_seconds"] == 5400

    def test_formatted_seconds_only(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="T",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=45,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "45s"

    def test_formatted_minutes(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="T",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=900,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "15m"

    def test_formatted_hours(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="T",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=7200,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_daily_stats()
        assert stats["total_formatted"] == "2h 0m"

    def test_excludes_other_days(self, db):
        yesterday = timezone.now() - timedelta(days=1)
        session = FocusSession.objects.create(
            label="Yesterday",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=3600,
            started_at=yesterday,
            stopped_at=yesterday,
        )
        # bypass auto_now_add so the filter sees it on the correct date
        FocusSession.objects.filter(pk=session.pk).update(created_at=yesterday)
        stats = services.get_daily_stats()
        assert stats["session_count"] == 0

    def test_stats_dict_has_required_keys(self):
        stats = services.get_daily_stats()
        for key in (
            "date",
            "session_count",
            "active_count",
            "total_seconds",
            "total_formatted",
            "sessions",
        ):
            assert key in stats


@pytest.mark.django_db
class TestGetWeeklyStats:
    def test_returns_seven_days(self):
        stats = services.get_weekly_stats()
        assert len(stats["days"]) == 7

    def test_last_day_is_today(self):
        stats = services.get_weekly_stats()
        today = timezone.now().date()
        assert stats["days"][-1]["date"] == today

    def test_first_day_is_six_days_ago(self):
        stats = services.get_weekly_stats()
        six_days_ago = timezone.now().date() - timedelta(days=6)
        assert stats["days"][0]["date"] == six_days_ago

    def test_today_flag_set_correctly(self):
        stats = services.get_weekly_stats()
        today_entries = [d for d in stats["days"] if d["is_today"]]
        assert len(today_entries) == 1
        assert today_entries[0]["date"] == timezone.now().date()

    def test_empty_db_all_zeros(self):
        stats = services.get_weekly_stats()
        assert stats["total_seconds"] == 0
        assert stats["total_sessions"] == 0
        assert stats["max_seconds"] == 0

    def test_bar_pct_zero_when_no_data(self):
        stats = services.get_weekly_stats()
        for day in stats["days"]:
            assert day["bar_pct"] == 0

    def test_bar_pct_max_day_is_100(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="Big",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=3600,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_weekly_stats()
        today_day = next(d for d in stats["days"] if d["is_today"])
        assert today_day["bar_pct"] == 100.0

    def test_bar_pct_proportional(self, db):
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        big = FocusSession.objects.create(
            label="Big",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=4000,
            started_at=now,
            stopped_at=now,
        )
        small = FocusSession.objects.create(
            label="Small",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=2000,
            started_at=yesterday,
            stopped_at=yesterday,
        )
        # bypass auto_now_add to place each session on the correct date
        FocusSession.objects.filter(pk=big.pk).update(created_at=now)
        FocusSession.objects.filter(pk=small.pk).update(created_at=yesterday)

        stats = services.get_weekly_stats()
        today_day = next(d for d in stats["days"] if d["is_today"])
        assert today_day["bar_pct"] == 100.0
        yesterday_day = stats["days"][-2]
        assert yesterday_day["bar_pct"] == 50.0

    def test_total_sessions_counts_all_week(self, db):
        now = timezone.now()
        for i in range(3):
            FocusSession.objects.create(
                label=f"S{i}",
                status=FocusSession.STATUS_COMPLETED,
                duration_seconds=600,
                started_at=now,
                stopped_at=now,
            )
        stats = services.get_weekly_stats()
        assert stats["total_sessions"] == 3

    def test_total_seconds_sums_week(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="S1",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=1800,
            started_at=now,
            stopped_at=now,
        )
        FocusSession.objects.create(
            label="S2",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=3600,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_weekly_stats()
        assert stats["total_seconds"] == 5400

    def test_total_formatted_minutes(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="S",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=1800,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_weekly_stats()
        assert stats["total_formatted"] == "30m"

    def test_total_formatted_hours(self, db):
        now = timezone.now()
        FocusSession.objects.create(
            label="S",
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=7200,
            started_at=now,
            stopped_at=now,
        )
        stats = services.get_weekly_stats()
        assert stats["total_formatted"] == "2h 0m"

    def test_day_name_format(self):
        stats = services.get_weekly_stats()
        for day in stats["days"]:
            assert day["day_name"] in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

    def test_required_keys_per_day(self):
        stats = services.get_weekly_stats()
        required = (
            "date",
            "day_name",
            "day_label",
            "total_seconds",
            "total_formatted",
            "session_count",
            "is_today",
            "bar_pct",
        )
        for day in stats["days"]:
            for key in required:
                assert key in day

    def test_empty_day_formatted_as_dash(self):
        stats = services.get_weekly_stats()
        for day in stats["days"]:
            assert day["total_formatted"] == "—"
