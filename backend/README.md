# Comicly Backend

Standalone FastAPI backend for Comicly.ai production backend work. The backend is API-only: it does not serve frontend assets and it does not migrate the existing root Node AI routes.

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

Phase 2 currently exposes:

- `GET /api/v1/coin-packages`

## Docker

Postgres and the backend app are managed by the backend Docker Compose file:

```powershell
cd backend
docker compose up --build
```

The Compose stack starts the FastAPI service and a local PostgreSQL service. Use `docker compose up -d` for detached local development.
The Docker image installs the lean runtime dependency set from `requirements-runtime.txt`; local test and lint tooling stays in `requirements.txt`.

Docker Compose is local-only. Production deployment should use a managed Postgres database such as Neon through Vercel Marketplace or equivalent provider integration.

## Environment

Copy `backend/.env.example` to `backend/.env` for local overrides.

| Variable | Meaning | Default |
| --- | --- | --- |
| `APP_NAME` | FastAPI application title | `Comicly API` |
| `APP_ENV` | Runtime environment label | `local` |
| `APP_DEBUG` | FastAPI debug flag | `false` |
| `DATABASE_URL` | SQLAlchemy async database URL | local Docker Postgres URL |
| `MIGRATION_DATABASE_URL` | Optional direct database URL for Alembic migrations | unset |
| `DATABASE_DIRECT_URL` | Optional direct database URL fallback for Alembic migrations | unset |
| `CORS_ORIGINS` | Comma-separated future frontend origins | unset |
| `FULL_PAGE_GENERATION_COST` | Future full page generation coin cost | `20` |
| `SCENE_REGENERATION_COST` | Future scene regeneration coin cost | `4` |
| `STARTER_COINS` | Future starter wallet coin amount | `100` |

For Vercel/Neon production:

- `DATABASE_URL` should be the Neon pooled connection URL converted to the async SQLAlchemy driver form, for example `postgresql+asyncpg://...`.
- `MIGRATION_DATABASE_URL` should be the Neon direct non-pooled URL for Alembic when available.
- Secrets such as `OPENROUTER_API_KEY`, OAuth secrets, session secrets, and storage credentials should be configured through environment variables, not committed files.

Later-phase variables such as OAuth secrets, OpenRouter keys, storage settings, and session secrets are documented in `.env.example` as references only. They are intentionally not required for startup yet.

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

Alembic is configured under `backend/`. It prefers `MIGRATION_DATABASE_URL`, then `DATABASE_DIRECT_URL`, and finally falls back to runtime `DATABASE_URL`.

```powershell
cd backend
python -m alembic current
python -m alembic revision -m "describe change"
python -m alembic upgrade head
```

The Phase 2 initial migration creates users, auth identity placeholders, wallets, comics, generation jobs, coin packages, and payment placeholders.

## Seed Data

Seed the default active coin package catalog after migrations:

```powershell
cd backend
python scripts/seed_coin_packages.py
```

The seed is idempotent and maintains these active packages:

- `coins_100`
- `coins_500`
- `coins_1000`

## Phase 1 Boundary

The existing root Node runtime still owns:

- `GET /api/health`
- `POST /api/ai-text`
- `POST /api/generate-comic-page`

FastAPI migration of those routes requires a later approved plan because it changes frontend/root runtime behavior. See `docs/phase1-boundary.md`.
