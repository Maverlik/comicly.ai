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

Phase 3 adds API-only auth/profile endpoints:

- `GET /api/v1/auth/google/login`
- `GET /api/v1/auth/google/callback`
- `GET /api/v1/auth/yandex/login`
- `GET /api/v1/auth/yandex/callback`
- `GET /api/v1/me`
- `PATCH /api/v1/me`
- `POST /api/v1/me/logout`

Phase 4 adds the authoritative wallet read endpoint:

- `GET /api/v1/wallet`

The wallet endpoint requires the product session cookie and returns the current database balance plus a short recent transaction list.

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
| `SESSION_SECRET` | Signing secret for temporary OAuth state cookie | local placeholder |
| `FRONTEND_CREATOR_URL` | Post-login redirect target | `https://comicly.ai/create.html` |
| `SESSION_COOKIE_NAME` | DB-backed product session cookie name | `comicly_session` |
| `SESSION_COOKIE_DOMAIN` | Optional cookie domain for shared parent domain deployment | unset |
| `SESSION_COOKIE_SECURE` | Whether product/OAuth cookies require HTTPS | `false` locally |
| `SESSION_COOKIE_SAMESITE` | Product/OAuth cookie SameSite policy | `lax` |
| `SESSION_LIFETIME_DAYS` | Product session lifetime | `30` |
| `GOOGLE_CLIENT_ID` | Google OAuth client id | unset |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | unset |
| `YANDEX_CLIENT_ID` | Yandex OAuth client id | unset |
| `YANDEX_CLIENT_SECRET` | Yandex OAuth client secret | unset |

For Vercel/Neon production:

- `DATABASE_URL` should be the Neon pooled connection URL converted to the async SQLAlchemy driver form, for example `postgresql+asyncpg://...`.
- `MIGRATION_DATABASE_URL` should be the Neon direct non-pooled URL for Alembic when available.
- `SESSION_SECRET`, OAuth secrets, `OPENROUTER_API_KEY`, and storage credentials should be configured through environment variables, not committed files.
- `SESSION_COOKIE_SECURE=true` should be used for production HTTPS.
- `SESSION_COOKIE_DOMAIN=.comicly.ai` is suitable when frontend is `comicly.ai`/`www.comicly.ai` and the backend API is `api.comicly.ai`.

OAuth provider secrets are intentionally optional at import/startup time so non-auth endpoints, tests, and health checks can run without live provider credentials. Live OAuth login routes require provider credentials when invoked.

Register these provider callback URLs for production:

- `https://api.comicly.ai/api/v1/auth/google/callback`
- `https://api.comicly.ai/api/v1/auth/yandex/callback`

Local callback URLs use the same paths on the local backend host, for example:

- `http://localhost:8000/api/v1/auth/google/callback`
- `http://localhost:8000/api/v1/auth/yandex/callback`

OAuth uses two different cookie concepts:

- Temporary OAuth state cookie: a short-lived signed Starlette session cookie used only to protect the redirect/callback flow.
- Product session cookie: an opaque random token in `comicly_session`; only its SHA-256 hash is stored in `user_sessions`, and the cookie is `HttpOnly`.

Avatar file upload is not implemented in Phase 3. The backend stores the provider-supplied `avatar_url` from OAuth and leaves real upload/storage for the later storage decision.

Later-phase variables such as OpenRouter keys and storage settings are documented in `.env.example` as references only. They are intentionally not required for startup yet.

## Wallet Ledger

Wallet balance is authoritative in PostgreSQL. Client-sent balances, owner ids, generation costs, and payment state must never be trusted for accounting.

Every balance change goes through `app.services.wallets` and creates a `wallet_transactions` row:

- grants and adjustments use positive amounts;
- generation debits use negative amounts;
- generation refunds use positive amounts linked to the failed/debited reference;
- each transaction stores `balance_after` for audit/debugging.

Current public wallet API:

- `GET /api/v1/wallet` returns `balance` and recent transactions for the authenticated user.

Phase 4 does not expose public debit/grant endpoints. Future billable generation code should call the wallet service with an `Idempotency-Key` value from the request. Missing billable idempotency maps to `IDEMPOTENCY_KEY_REQUIRED`; duplicate keys replay the existing logical operation and do not double-charge.

Server-controlled generation costs are:

- full page generation: `FULL_PAGE_GENERATION_COST`, default `20`;
- scene regeneration: `SCENE_REGENERATION_COST`, default `4`.

If a user cannot cover a debit, the service returns `INSUFFICIENT_COINS` with HTTP status `409` and does not create a debit row. If a future OpenRouter generation fails after a debit, the caller should create one idempotent refund transaction rather than silently editing the original debit.

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
