# Phase 1: Backend Foundation And Static Safety - Research

**Researched:** 2026-04-26
**Phase:** 1 - Backend Foundation And Static Safety
**Status:** Ready for planning

## Research Summary

Phase 1 should create a standalone API-only Python backend foundation under `backend/`. It should not migrate the frontend, should not implement OAuth/wallet/comic business features, and should not modify root/frontend files without explicit user approval.

The locked stack from `01-CONTEXT.md` is:

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2 async ORM patterns
- Alembic migrations
- `asyncpg`
- `pip + requirements.txt`
- Pydantic Settings
- Pytest + HTTPX/FastAPI test client patterns
- Ruff for lint/format
- Docker Compose with backend app + Postgres

The most important planning correction: prior project research recommended Node/Express, but that recommendation is superseded for this phase. The backend is intentionally independent from the existing frontend and prototype `server.js`.

## Source Of Truth

Downstream planning must treat `backend/BACKEND_TZ.md` as the backend requirements source of truth. For Phase 1, only foundation pieces from that spec are in scope:

- backend becomes its own service;
- environment variables are documented;
- migrations and clean startup path are prepared;
- API must be safe and production-shaped;
- no secrets in client code;
- no accidental static file exposure;
- later phases can build auth, wallet, profiles, comic persistence, OpenRouter generation, and deployment on this base.

## Recommended Backend Directory Structure

Plan should create or standardize only files inside `backend/`.

Recommended shape:

```text
backend/
  app/
    __init__.py
    main.py                 # FastAPI app factory / app instance
    api/
      __init__.py
      health.py             # /health and /ready routes
    core/
      __init__.py
      config.py             # Pydantic Settings
      errors.py             # stable API error shapes / exception handlers
    db/
      __init__.py
      base.py               # SQLAlchemy DeclarativeBase
      session.py            # async engine/sessionmaker
      health.py             # readiness DB ping helper
  alembic/
    env.py
    script.py.mako
    versions/
  tests/
    conftest.py
    test_health.py
    test_static_safety.py
    test_config.py
  alembic.ini
  docker-compose.yml
  Dockerfile
  .dockerignore
  .env.example
  requirements.txt
  README.md
```

This keeps Phase 1 backend-only and leaves root `server.js`, `index.html`, `create.html`, `scripts/`, and CSS untouched.

## Dependencies

Use a single `requirements.txt` for MVP simplicity, per user decision.

Suggested baseline:

```text
fastapi
uvicorn[standard]
pydantic-settings
sqlalchemy[asyncio]
asyncpg
alembic
httpx
pytest
pytest-asyncio
ruff
```

Notes:

- `httpx` is included because it is useful for tests now and future OpenRouter integration later.
- `sqlalchemy[asyncio]` follows SQLAlchemy's async support guidance.
- Avoid adding Authlib in Phase 1 unless planner chooses to document it only. OAuth implementation belongs to Phase 3.
- Avoid adding payment/storage/auth dependencies in Phase 1.

## Docker Strategy

Phase 1 should include Docker Compose for both backend app and Postgres.

Recommended services:

- `backend-api`: builds from `backend/Dockerfile`, runs Uvicorn, mounts source for local development if appropriate.
- `backend-postgres`: PostgreSQL with a named volume.

Recommended defaults:

- Backend port: `8000`.
- Postgres internal port: `5432`.
- Environment from `backend/.env` or Compose env entries.
- `DATABASE_URL` should use async SQLAlchemy URL format for app runtime, for example `postgresql+asyncpg://...`.
- If Alembic needs a sync URL, either derive it in `alembic/env.py` or document separate handling.

Planning should include `.dockerignore` so local caches, virtualenvs, tests cache, and secrets are not copied into the image.

## FastAPI App Pattern

Use an app factory or a clear app instance in `backend/app/main.py`.

Recommended:

- `create_app()` configures FastAPI, exception handlers, and routers.
- `app = create_app()` for Uvicorn import path.
- Include only health/readiness router in Phase 1.
- Do not mount `StaticFiles`.
- Do not serve frontend assets.
- Business routers should be reserved for later phases under `/api/v1/...`.

Health endpoints:

- `GET /health`: lightweight process health, no DB dependency, stable JSON such as `{ "status": "ok" }`.
- `GET /ready`: readiness check, should verify DB connectivity once DB wiring exists. If DB is unreachable, return a non-2xx status with stable error code.

## Config And Env

Use Pydantic Settings to load env configuration.

Phase 1 config should include foundation values only:

- `APP_ENV`
- `APP_NAME`
- `APP_DEBUG`
- `DATABASE_URL`
- optional `CORS_ALLOWED_ORIGINS` placeholder if needed later, but avoid enabling broad CORS unless required.

Do not require all future variables from `backend/BACKEND_TZ.md` at app startup in Phase 1. Document future env vars in README or `.env.example` as later-phase placeholders if useful:

- `SESSION_SECRET`
- `APP_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `YANDEX_CLIENT_ID`
- `YANDEX_CLIENT_SECRET`
- `OPENROUTER_API_KEY`
- storage variables
- `STARTER_COINS`

Rationale: Phase 1 should be runnable before OAuth/OpenRouter/storage exist.

## Error Shape

Phase 1 should establish stable JSON error responses without overbuilding the full error taxonomy.

Recommended shape:

```json
{
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "Database is not ready"
  }
}
```

Planner should include tasks for:

- custom exception or helper response for app-level errors;
- validation error behavior review;
- tests for readiness failure if practical;
- no sensitive config details in errors.

## SQLAlchemy And Alembic Foundation

Phase 1 should wire the database foundation without implementing full business schema.

Recommended:

- `app/db/base.py` defines `DeclarativeBase`.
- `app/db/session.py` creates async engine and async sessionmaker from `DATABASE_URL`.
- `app/db/health.py` runs a simple `SELECT 1` readiness check.
- Alembic is initialized and imports metadata from `app.db.base`.
- First migration can either be an empty baseline or create a minimal harmless extension-less baseline. Full users/wallet/comics/payment tables belong to Phase 2.

Do not create the full schema from `backend/BACKEND_TZ.md` in Phase 1. That belongs to Phase 2.

## Static Safety

Because the backend is API-only, static safety is mostly a negative guarantee:

- no `StaticFiles` mount;
- no route that reads arbitrary file paths;
- no root repository serving;
- no direct access to `.env`, `.planning/`, `backend/BACKEND_TZ.md`, `package.json`, or frontend files through backend routes.

Tests should assert representative private/static paths return `404` or equivalent:

- `/.env`
- `/.planning/PROJECT.md`
- `/backend/BACKEND_TZ.md`
- `/package.json`
- `/index.html`
- `/create.html`

This satisfies the intent of `SAFE-01` for the new API-only backend without modifying the existing prototype root `server.js`.

## Testing Strategy

Use Pytest and HTTPX/FastAPI testing patterns.

Phase 1 tests should cover:

- `GET /health` returns success without DB dependency.
- `GET /ready` returns success when test DB is reachable.
- `GET /ready` returns stable error when DB check fails, if practical to simulate.
- app starts/imports with test settings.
- representative static/private paths are not served.
- validation/error shape is stable for at least one known error path.

Test setup options:

- Use the Docker Postgres service for integration tests.
- Keep unit-like app tests fast with dependency overrides where possible.
- Do not mock away all DB readiness behavior; `/ready` should be verified against real or controlled DB behavior.

## Lint And Format

Use Ruff for both linting and formatting.

Recommended commands documented in `backend/README.md`:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Optionally include a local formatting command:

```powershell
python -m ruff format .
```

## Verification Commands

Plans should require enough commands to prove foundation works:

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r requirements.txt
.\\.venv\\Scripts\\python -m pytest
.\\.venv\\Scripts\\python -m ruff check .
.\\.venv\\Scripts\\python -m ruff format --check .
docker compose up --build
```

Exact activation commands may be documented for PowerShell. Docker command should be scoped to `backend/`.

## Planning Risks

1. **Scope creep into business features.** Avoid implementing OAuth, wallet tables, comic APIs, OpenRouter calls, or frontend integration in Phase 1.
2. **Accidental root/frontend changes.** Plans must only modify `backend/` and `.planning/` artifacts unless user approval is explicitly requested.
3. **Over-requiring future env vars.** App should not fail because OAuth/OpenRouter/storage values are absent in Phase 1.
4. **Alembic overreach.** Phase 1 should set up migrations, not design the whole production schema.
5. **Static safety ambiguity.** For standalone API-only backend, prove that this backend does not serve static/private files. Do not try to fix root `server.js` unless separately approved.
6. **Docker friction.** Compose should run backend + Postgres in a clear way; README should make commands obvious.

## Recommended Plan Breakdown

Plan 1: Python/FastAPI project scaffold and config foundation.

- Create backend package structure.
- Add requirements, `.env.example`, Dockerfile, docker-compose.
- Add Pydantic Settings and app factory.

Plan 2: Health/readiness, DB wiring, Alembic foundation.

- Add SQLAlchemy async engine/session.
- Add `/health` and `/ready`.
- Initialize Alembic against metadata.
- Add readiness DB ping.

Plan 3: Quality gates, static safety tests, documentation.

- Add pytest tests for health/readiness/static safety/config.
- Add Ruff commands/config if needed.
- Add README with local, Docker, test, lint, migration commands.

Parallelization:

- Plan 1 should happen first.
- Plan 2 depends on Plan 1.
- Plan 3 depends on Plans 1 and 2.

## Validation Architecture

Dimension 1 - Scope:

- Plans must only touch `backend/` plus phase planning docs.
- No frontend/root runtime files may be modified.

Dimension 2 - Requirement Coverage:

- `SAFE-01`: covered by API-only static safety posture and tests for representative private paths.
- `SAFE-02`: covered by modular FastAPI backend structure in `backend/app`.
- `SAFE-03`: covered by stable JSON error response helper/handler.
- `SAFE-04`: covered by FastAPI/Pydantic validation scaffolding and at least one validation/error test.
- `SAFE-05`: interpreted for new standalone backend as documenting migration boundary and not breaking current root prototype; old AI route migration is deferred because backend is API-only and frontend untouched.
- `OPS-06`: covered by production-safe `/health` and `/ready` without secret/config leakage.
- `TEST-01`: covered by Pytest tests for static safety, API errors, and health/readiness.

Dimension 3 - Verification:

- `pytest` must pass.
- `ruff check` must pass.
- `ruff format --check` must pass.
- Docker Compose app + Postgres must start, or the plan must explicitly document why local environment prevents runtime verification.

Dimension 4 - Deferral Integrity:

- OAuth, wallet, comic persistence, payments, OpenRouter generation, and frontend integration must appear only as future-phase notes, not implementation tasks.

## References

- `backend/BACKEND_TZ.md`
- `.planning/phases/01-backend-foundation-and-static-safety/01-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/codebase/CONCERNS.md`
- FastAPI docs: `https://fastapi.tiangolo.com/`
- SQLAlchemy asyncio docs: `https://docs.sqlalchemy.org/20/orm/extensions/asyncio.html`
- SQLAlchemy PostgreSQL asyncpg docs: `https://docs.sqlalchemy.org/en/20/dialects/postgresql.html`
- Alembic docs: `https://alembic.sqlalchemy.org/`
- Authlib FastAPI OAuth docs for later phase awareness: `https://docs.authlib.org/en/v1.6.2/client/fastapi.html`

---

## RESEARCH COMPLETE

Research artifact written for Phase 1. Ready for planning.
