# FocusFlow

A production-grade focus session tracker built with Django 5, HTMX, and AlpineJS. Sessions are created, started, and stopped via partial-page HTMX requests with a live 1-second polling timer. No JavaScript framework required beyond Alpine for modal state.

## Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12, Django 5.x |
| Frontend | HTMX 2.x, AlpineJS 3.x, vanilla CSS |
| API layer | Django REST Framework (throttled) |
| Reverse proxy | Nginx 1.27 |
| Container | Docker (multi-stage, non-root) |
| Database | SQLite (volume-mounted) |
| CI | GitHub Actions |

## Quick Start

```bash
cp .env.example .env   # edit SECRET_KEY and CSRF_TRUSTED_ORIGINS
docker compose up --build
```

Application: `http://localhost:8080`
Health check: `http://localhost:8080/health/`

## Project Layout

```
apps/
  core/         health endpoint, 404/500 handlers, root redirect
  sessions/     FocusSession model, services, views, HTMX partials
config/
  settings/     base / development / production
  urls.py
nginx/          nginx.conf, default.conf
tests/          pytest suite (160 tests, 98% coverage)
.github/
  workflows/
    ci.yml      lint → test + security → docker build
```

## Documentation

| Document | Contents |
|---|---|
| [Architecture](docs/architecture.md) | System design, data model, request lifecycle |
| [Development](docs/development.md) | Local setup, tooling, conventions |
| [Testing](docs/testing.md) | Test strategy, coverage, running the suite |
| [Deployment](docs/deployment.md) | Docker, env vars, production checklist |

## CI Status

Pipeline: lint → test (parallel with security) → docker build.
All four jobs must pass before merge to `develop`.
