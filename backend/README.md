# Comicly Backend

Standalone FastAPI backend for Comicly.ai production backend work. Phase 1 is API-only: it does not serve frontend assets and it does not migrate the existing root Node AI routes.

## Local Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Run the API locally:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend port defaults to `8000`. Health endpoints are unprefixed:

- `GET /health`
- `GET /ready`

Future business APIs belong under `/api/v1/`.

## Docker

Postgres and the backend app are managed by the backend Docker Compose file:

```powershell
cd backend
docker compose up --build
```

The Compose stack starts the FastAPI service and a local PostgreSQL service. Use `docker compose up -d` for detached local development.

## Environment

Copy `backend/.env.example` to `backend/.env` for local overrides. Phase 1 only requires foundation settings:

| Variable | Meaning | Default |
| --- | --- | --- |
| `APP_NAME` | FastAPI application title | `Comicly API` |
| `APP_ENV` | Runtime environment label | `local` |
| `APP_DEBUG` | FastAPI debug flag | `false` |
| `DATABASE_URL` | SQLAlchemy async database URL | local Docker Postgres URL |

Later-phase variables such as OAuth secrets, OpenRouter keys, storage settings, session secrets, and starter coin amounts are documented in `.env.example` as references only. They are intentionally not required for Phase 1 startup.

## Quality Gates

Run these from `backend/`:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Format code with:

```powershell
python -m ruff format .
```

Root/frontend runtime files must remain untouched during Phase 1. This guard command should produce no output after backend-only work:

```powershell
git -C .. diff --name-only -- server.js package.json index.html create.html scripts styles.css creator.css .env.example
```

## Migrations

Alembic is configured under `backend/` and reads the same `DATABASE_URL` setting as the app.

```powershell
cd backend
python -m alembic current
python -m alembic revision -m "describe change"
python -m alembic upgrade head
```

Business schema migrations for users, wallets, comics, payments, and generation results are deferred to later phases.

## Phase 1 Boundary

The existing root Node runtime still owns:

- `GET /api/health`
- `POST /api/ai-text`
- `POST /api/generate-comic-page`

FastAPI migration of those routes requires a later approved plan because it changes frontend/root runtime behavior. See `docs/phase1-boundary.md`.
