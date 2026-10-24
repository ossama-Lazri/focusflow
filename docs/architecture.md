# Architecture

## System Overview

```
Browser ──► Nginx :80 ──► Gunicorn :8000 ──► Django app
                │
                └──► /static/ (served directly from shared volume)
```

Nginx terminates HTTP, enforces rate limits, and serves static assets from a Docker volume shared with the Django container. Gunicorn runs 2 workers with HTTP/1.1 keepalive to Nginx. SQLite is stored on a named Docker volume (`sqlite_data`) mounted at `/app/data`.

## Request Lifecycle

Standard HTMX flow for a mutating action (e.g. start session):

1. Browser sends `POST /sessions/<pk>/start/` with `HX-Request: true` header.
2. Nginx applies the `sessions` rate limit zone (30 req/min per IP, burst 20).
3. Django view calls `services.start_session(session)` — all mutation logic is in `services.py`.
4. View renders `sessions/partials/_session_row.html` and sets `HX-Trigger: sessionStarted`.
5. HTMX swaps the target row; the `sessionStarted` trigger fires a dashboard refresh listener.

Live timer polling: `_session_timer.html` uses `hx-trigger="every 1s" hx-swap="outerHTML"` targeting `GET /sessions/<pk>/timer/`. The partial re-renders elapsed time server-side each second.

## Application Modules

### `apps.core`
- Root redirect (`/` → `/dashboard/`)
- `/health/` endpoint — returns 200 with `{"status": "ok"}`
- Custom 404 / 500 handlers

### `apps.sessions`
Separation of concerns is strict:

| Layer | Responsibility |
|---|---|
| `models.py` | Schema, `duration_formatted`, `elapsed_seconds`, `elapsed_formatted` properties |
| `services.py` | All DB mutations and stat aggregations |
| `views.py` | HTTP glue — validates input, calls services, returns response |

Views contain no business logic. Services contain no HTTP concerns.

## Data Model

```
FocusSession
├── label            CharField(255)
├── status           CharField  idle | active | completed
├── started_at       DateTimeField nullable
├── stopped_at       DateTimeField nullable
├── duration_seconds IntegerField default=0
├── created_at       DateTimeField auto
└── updated_at       DateTimeField auto
```

**State machine:**

```
idle ──► active ──► completed
```

Only one session can be `active` at a time. `start_session()` stops any existing active session before starting the new one. `stop_session()` is a no-op on non-active sessions.

`duration_seconds` is written on stop: `int((stopped_at - started_at).total_seconds())`. The `elapsed_seconds` property computes live elapsed time for active sessions; `duration_seconds` for others.

## Settings Hierarchy

```
config/settings/base.py        shared across all environments
config/settings/development.py DEBUG=True, SQLite at BASE_DIR, insecure defaults
config/settings/production.py  DEBUG=False, WhiteNoise, security headers, env-driven
```

`base.py` reads `SECRET_KEY` with no default — app fails fast without it. `development.py` provides its own default via `python-decouple` for local convenience. `production.py` requires `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` from environment.

## Security Controls

| Control | Implementation |
|---|---|
| Secret management | `python-decouple`, no defaults in production |
| CSRF | `CsrfViewMiddleware`, `CSRF_COOKIE_SECURE` env-driven |
| Clickjacking | `X-Frame-Options: DENY` (Django + Nginx) |
| Rate limiting | Nginx: 60 req/min general, 30 req/min `/sessions/` |
| HSTS | Env-driven `SECURE_HSTS_SECONDS` (0 in dev) |
| Static files | WhiteNoise with `CompressedManifestStaticFilesStorage` |
| Container | Non-root `appuser` (uid 1001), read-only Nginx config mounts |

## Frontend Architecture

No build step. Assets are plain files in `static/`.

- **CSS** — `static/css/app.css`: CSS custom properties for theming, component-scoped rules. No utility classes.
- **JS** — `static/js/app.js`: CSRF injection for HTMX, toast system, AlpineJS modal store.
- **HTMX** handles all data operations. AlpineJS manages ephemeral UI state (modals, dropdowns).
- Templates follow Django's `APP_DIRS=True` discovery — app templates in `apps/<app>/templates/<app>/`.
