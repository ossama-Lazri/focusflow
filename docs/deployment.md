# Deployment

## Requirements

- Docker + Docker Compose v2
- A `.env` file with all required variables (see below)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated hostnames, e.g. `yourdomain.com,www.yourdomain.com` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Comma-separated origins with scheme, e.g. `https://yourdomain.com` |
| `DATABASE_PATH` | ✅ | Absolute path inside container, e.g. `/app/data/db.sqlite3` |
| `SECURE_SSL_REDIRECT` | — | `True` if Nginx/LB handles TLS termination upstream (default `False`) |
| `SECURE_HSTS_SECONDS` | — | HSTS max-age in seconds. Set `0` until TLS is confirmed working (default `31536000`) |
| `SESSION_COOKIE_SECURE` | — | `True` in production behind HTTPS (default `True`) |
| `CSRF_COOKIE_SECURE` | — | `True` in production behind HTTPS (default `True`) |
| `DJANGO_LOG_LEVEL` | — | Django logger level (default `WARNING`) |

> [!CAUTION]
> Never commit `.env` to version control. The `.gitignore` excludes it. Rotate `SECRET_KEY` if it is ever exposed — all sessions are immediately invalidated.

## Starting the Stack

```bash
cp .env.example .env
# Fill in SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DATABASE_PATH
docker compose up --build -d
```

Nginx starts only after the `web` service passes its health check (`/health/`). The health check polls every 30 seconds with a 40-second start period.

## Container Architecture

| Service | Image | Port | Notes |
|---|---|---|---|
| `web` | built from `Dockerfile` | 8000 (internal) | Gunicorn, 2 workers, non-root uid 1001 |
| `nginx` | `nginx:1.27-alpine` | 8080 → 80 | Rate limiting, static files, proxy |

**Volumes:**

| Volume | Mount | Purpose |
|---|---|---|
| `sqlite_data` | `/app/data` (web) | Persistent database |
| `staticfiles` | `/app/staticfiles` (web) + `/usr/share/nginx/html/static` (nginx) | Shared static assets |

Static files are collected by `entrypoint.sh` (`collectstatic --noinput --clear`) on every container start. Nginx serves them directly; Django does not serve static files in production.

## Dockerfile

Multi-stage build:
1. **builder** — installs dependencies as wheels from `requirements.txt`
2. **runtime** — copies wheels, installs offline, copies app source

The `entrypoint.sh` script runs `migrate` and `collectstatic` before starting Gunicorn. CRLF line endings are stripped during build (`tr -d '\r'`) to avoid exec format errors on Linux when developed on Windows.

## Updating

```bash
git pull origin main
docker compose up --build -d
```

`migrate` runs automatically on container start. There is no downtime handling for SQLite — stop the old container and start the new one. For zero-downtime deploys, a load balancer with multiple replicas is required (not applicable to SQLite).

## Backup

SQLite database is in the `sqlite_data` Docker volume. Back up with:

```bash
docker compose exec web python manage.py dumpdata --natural-foreign --indent 2 > backup.json
```

Or copy the raw file:

```bash
docker run --rm -v focusflow_sqlite_data:/data -v $(pwd):/backup alpine \
  cp /data/db.sqlite3 /backup/db.sqlite3.bak
```

## Production Checklist

- [ ] `SECRET_KEY` is unique and not the development default
- [ ] `ALLOWED_HOSTS` contains only your domain(s)
- [ ] `CSRF_TRUSTED_ORIGINS` contains only your origin(s) with correct scheme
- [ ] `SECURE_HSTS_SECONDS` is `0` until TLS is confirmed end-to-end
- [ ] TLS termination is handled upstream (load balancer or Nginx with certificates)
- [ ] `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` once HTTPS is active
- [ ] `SECURE_HSTS_SECONDS` set to `31536000` once HTTPS is stable
- [ ] Database backup strategy in place
- [ ] Log aggregation configured (`DJANGO_LOG_LEVEL`, stdout captured by Docker)
