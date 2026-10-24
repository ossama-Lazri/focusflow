import pytest
from datetime import timedelta
from django.utils import timezone
from apps.sessions.models import FocusSession


@pytest.mark.django_db
class TestFocusSessionStr:
    def test_str_idle(self, idle_session):
        assert str(idle_session) == 'Deep work: feature planning (idle)'

    def test_str_active(self, active_session):
        assert str(active_session) == 'Active: code review (active)'

    def test_str_completed(self, completed_session):
        assert str(completed_session) == 'Completed: design sprint (completed)'


@pytest.mark.django_db
class TestFocusSessionDefaults:
    def test_default_status_is_idle(self):
        session = FocusSession.objects.create(label='Test')
        assert session.status == FocusSession.STATUS_IDLE

    def test_default_duration_is_zero(self):
        session = FocusSession.objects.create(label='Test')
        assert session.duration_seconds == 0

    def test_started_at_defaults_null(self):
        session = FocusSession.objects.create(label='Test')
        assert session.started_at is None

    def test_stopped_at_defaults_null(self):
        session = FocusSession.objects.create(label='Test')
        assert session.stopped_at is None

    def test_created_at_auto_set(self):
        session = FocusSession.objects.create(label='Test')
        assert session.created_at is not None

    def test_updated_at_auto_set(self):
        session = FocusSession.objects.create(label='Test')
        assert session.updated_at is not None


@pytest.mark.django_db
class TestFocusSessionOrdering:
    def test_newest_first(self):
        s1 = FocusSession.objects.create(label='First')
        s2 = FocusSession.objects.create(label='Second')
        sessions = list(FocusSession.objects.all())
        assert sessions[0].pk == s2.pk
        assert sessions[1].pk == s1.pk


@pytest.mark.django_db
class TestDurationFormatted:
    def test_seconds_only(self):
        session = FocusSession(label='T', duration_seconds=45)
        assert session.duration_formatted == '45s'

    def test_zero_seconds(self):
        session = FocusSession(label='T', duration_seconds=0)
        assert session.duration_formatted == '0s'

    def test_minutes_and_seconds(self):
        session = FocusSession(label='T', duration_seconds=185)
        assert session.duration_formatted == '3m 5s'

    def test_exact_minute(self):
        session = FocusSession(label='T', duration_seconds=60)
        assert session.duration_formatted == '1m 0s'

    def test_hours_minutes_seconds(self):
        session = FocusSession(label='T', duration_seconds=3661)
        assert session.duration_formatted == '1h 1m 1s'

    def test_exact_hour(self):
        session = FocusSession(label='T', duration_seconds=3600)
        assert session.duration_formatted == '1h 0m 0s'

    def test_multiple_hours(self):
        session = FocusSession(label='T', duration_seconds=7322)
        assert session.duration_formatted == '2h 2m 2s'


@pytest.mark.django_db
class TestElapsedSeconds:
    def test_idle_returns_duration_seconds(self, idle_session):
        assert idle_session.elapsed_seconds == 0

    def test_completed_returns_duration_seconds(self, completed_session):
        assert completed_session.elapsed_seconds == 5400

    def test_active_returns_live_elapsed(self, active_session):
        elapsed = active_session.elapsed_seconds
        assert elapsed >= 1800
        assert elapsed < 1860

    def test_active_without_started_at_returns_zero(self, db):
        session = FocusSession.objects.create(
            label='Broken',
            status=FocusSession.STATUS_ACTIVE,
            started_at=None,
        )
        assert session.elapsed_seconds == 0


@pytest.mark.django_db
class TestElapsedFormatted:
    def test_completed_shows_hh_mm_ss(self, completed_session):
        assert completed_session.elapsed_formatted == '01:30:00'

    def test_idle_shows_mm_ss(self, idle_session):
        assert idle_session.elapsed_formatted == '00:00'

    def test_active_shows_running_time(self, active_session):
        result = active_session.elapsed_formatted
        assert ':' in result

    def test_format_under_one_hour(self, db):
        session = FocusSession.objects.create(
            label='T',
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=125,
        )
        assert session.elapsed_formatted == '02:05'

    def test_format_over_one_hour(self, db):
        session = FocusSession.objects.create(
            label='T',
            status=FocusSession.STATUS_COMPLETED,
            duration_seconds=3723,
        )
        assert session.elapsed_formatted == '01:02:03'


@pytest.mark.django_db
class TestStatusConstants:
    def test_status_constants(self):
        assert FocusSession.STATUS_IDLE == 'idle'
        assert FocusSession.STATUS_ACTIVE == 'active'
        assert FocusSession.STATUS_COMPLETED == 'completed'

    def test_status_choices_labels(self):
        choices_dict = dict(FocusSession.STATUS_CHOICES)
        assert choices_dict['idle'] == 'Idle'
        assert choices_dict['active'] == 'Active'
        assert choices_dict['completed'] == 'Completed'
