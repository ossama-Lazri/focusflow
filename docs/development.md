# Development

## Prerequisites

- Python 3.12
- pip / virtualenv
- Git

Docker is only required for running the full production stack locally. All development iteration runs without it.

## Local Setup

```bash
git clone https://github.com/ossama-Lazri/focusflow.git
cd focusflow
python3.12 -m venv focusflow-venv
source focusflow-venv/bin/activate        # Windows WSL: same command
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                      # defaults work for development
python manage.py migrate
python manage.py runserver
```

`DJANGO_SETTINGS_MODULE` defaults to `config.settings.development` via `manage.py`. No override needed locally.

## Environment Variables

Only `SECRET_KEY` is required in development (`.env.example` includes a safe default). All other vars have development-safe defaults.

Production-required vars are documented in [deployment.md](deployment.md).

## Code Style

| Tool | Config | Enforced by |
|---|---|---|
| black | `pyproject.toml` defaults, line-length 88 | CI lint job |
| flake8 | `.flake8` | CI lint job |

Run both locally before pushing:

```bash
black apps/ config/ tests/
flake8 apps/ config/ tests/
```

**Never manually line-wrap Python files** — black owns formatting. Edit, then run `black`.

`.flake8` key rules:
- `max-line-length = 88` (matches black)
- `per-file-ignores = config/settings/*.py: F401,F403,F405` — wildcard imports in settings are intentional
- `extend-ignore = E501,W503,W504`

## Adding a Feature

1. Branch from `develop`: `git checkout -b feature/<name>`
2. All business logic goes in `services.py` — views stay thin.
3. Add tests in `tests/` before or alongside the feature.
4. Run `black`, `flake8`, `pytest` locally — all must pass.
5. Open a PR against `develop`. CI runs automatically.

## Django Admin

Admin is registered for `FocusSession` at `/admin/`. Create a superuser with:

```bash
python manage.py createsuperuser
```

## Dependency Management

Runtime deps: `requirements.txt`
Dev/CI deps: `requirements-dev.txt`

To add a runtime dependency: add to `requirements.txt` with a minimum version constraint (`>=x.y`). Pin if the package has a history of breaking changes.
