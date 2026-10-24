# Testing

## Overview

| Metric | Value |
|---|---|
| Total tests | 160 |
| Coverage | 98% |
| Runner | pytest + pytest-django |
| Settings | `config.settings.development` |
| DB | SQLite in-memory (per Django test runner) |

## Running the Suite

```bash
pytest                          # full suite with coverage
pytest tests/test_services.py   # single file
pytest -k "test_stop"           # filter by name
pytest --no-cov                 # skip coverage (faster iteration)
```

Coverage threshold: `--cov-fail-under=80` (configured in `pytest.ini`). CI fails below this threshold.

## Test Structure

```
tests/
  conftest.py          shared fixtures
  test_models.py       FocusSession properties and state constants
  test_services.py     service-layer unit tests with DB
  test_statistics.py   daily/weekly aggregation and formatting
  test_views.py        HTTP response codes, templates, HTMX headers
```

## Test Strategy

**Services** (`test_services.py`, `test_statistics.py`): Each service function is tested in isolation against a real SQLite test DB. No mocking — tests exercise the actual ORM queries. This catches aggregation bugs that unit-mocked tests would miss.

**Views** (`test_views.py`): Uses Django's `Client`. HTMX requests are simulated with `HTTP_HX_REQUEST=true`. Tests assert status codes, template names, context keys, and response headers (`HX-Trigger`, `HX-Redirect`). No UI/browser testing.

**Models** (`test_models.py`): Property logic only — `duration_formatted`, `elapsed_seconds`, `elapsed_formatted`. No DB interaction needed; objects are instantiated directly.

## Fixtures

`conftest.py` provides:

| Fixture | Scope | Description |
|---|---|---|
| `client` | function | Django test client |
| `idle_session` | function | Unsaved `FocusSession(status='idle')` |
| `active_session` | function | DB-persisted session in active state |
| `completed_session` | function | DB-persisted session with duration |

## What Is Not Tested

- **Templates rendering correctness** — view tests assert template name, not HTML structure. CSS/layout changes don't break CI.
- **JavaScript** — no JS test runner. HTMX/Alpine behaviour is covered by manual testing.
- **Admin** — Django admin is not tested; it's a thin registration with no custom logic.
- **Nginx config** — integration-tested manually via `docker compose up`.

## CI Integration

The `test` job in `.github/workflows/ci.yml`:
1. Installs `requirements.txt` + `requirements-dev.txt`
2. Runs `pytest` (includes coverage report)
3. Uploads `coverage.xml` as an artifact (7-day retention)

The `security` job runs `bandit -r apps/ config/ -ll -ii --skip B105` and `pip-audit -r requirements.txt` in parallel with `test`.
