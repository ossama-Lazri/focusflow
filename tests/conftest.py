import pytest
from datetime import timedelta
from django.utils import timezone
from apps.sessions.models import FocusSession


@pytest.fixture
def idle_session(db):
    return FocusSession.objects.create(label='Deep work: feature planning')


@pytest.fixture
def active_session(db):
    return FocusSession.objects.create(
        label='Active: code review',
        status=FocusSession.STATUS_ACTIVE,
        started_at=timezone.now() - timedelta(minutes=30),
    )


@pytest.fixture
def completed_session(db):
    now = timezone.now()
    return FocusSession.objects.create(
        label='Completed: design sprint',
        status=FocusSession.STATUS_COMPLETED,
        started_at=now - timedelta(hours=1, minutes=30),
        stopped_at=now,
        duration_seconds=5400,
    )


@pytest.fixture
def htmx_headers():
    return {'HTTP_HX_REQUEST': 'true', 'HTTP_HX_CURRENT_URL': 'http://testserver/dashboard/'}


@pytest.fixture
def session_factory(db):
    def _factory(label='Session', status=FocusSession.STATUS_IDLE, duration_seconds=0,
                 started_at=None, stopped_at=None):
        return FocusSession.objects.create(
            label=label,
            status=status,
            duration_seconds=duration_seconds,
            started_at=started_at,
            stopped_at=stopped_at,
        )
    return _factory
