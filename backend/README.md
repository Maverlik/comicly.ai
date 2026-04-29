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

Phase 5 adds authenticated private comic persistence:

- `POST /api/v1/comics`
- `GET /api/v1/comics`
- `GET /api/v1/comics?include_archived=true`
- `GET /api/v1/comics/{comic_id}`
- `PATCH /api/v1/comics/{comic_id}`
- `DELETE /api/v1/comics/{comic_id}`
- `PUT /api/v1/comics/{comic_id}/scenes`
- `PUT /api/v1/comics/{comic_id}/pages`

Comic APIs require the product session cookie. They are owner-scoped: users can only list, open, update, archive, and replace scenes/pages for their own comics.

Phase 6 adds authenticated generation APIs:

- `POST /api/v1/generations`
- `POST /api/v1/ai-text`

`POST /api/v1/generations` is the synchronous MVP path for full comic page generation. It requires the product session cookie and an `Idempotency-Key` header. The request accepts creator-compatible fields such as `story`, `characters`, `style`, `tone`, `selectedScene`, `scenes`, `dialogue`, `caption`, `layout`, plus backend persistence fields `comic_id`, optional `scene_id`, `page_number`, and optional `model_id`.

The generation response contains only durable metadata: job, page, updated balance, and `image_url`. It must not return provider base64 image data. Generated images are copied to Vercel Blob before success is returned.

`POST /api/v1/ai-text` is authenticated and free for the MVP. It supports `enhance`, `dialogue`, `caption`, and `scenes` tasks through the server-side OpenRouter service. It does not create generation jobs or wallet transactions.

## Docker

Postgres and the backend app are managed by the backend Docker Compose file:

```powershell
cd backend
docker compose up --build
```

The Compose stack starts the FastAPI service and a local PostgreSQL service. Use `docker compose up -d` for detached local development.
The Docker image installs the lean runtime dependency set from `requirements-runtime.txt`; local test and lint tooling stays in `requirements.txt`.

Docker Compose is local-only. Production deployment should use a managed Postgres database such as Neon through Vercel Marketplace or equivalent provider integration.

## Vercel Deployment Boundary

Production MVP deployment uses two separate Vercel projects from the same repository:

- frontend project rooted at the repository root, serving `comicly.ai` and `www.comicly.ai`;
- backend project rooted at `backend/`, serving the API on `api.comicly.ai`.

The root frontend project builds an explicit static output directory from an allow-list of public files. Do not deploy the repository root as a raw static directory, because root-level files such as `.env`, `.planning/`, `backend/`, and package metadata are not public assets.

The backend project is a standalone FastAPI service. Vercel Python runtime support is currently Beta, so keep business logic portable and isolated from Vercel-only features. Docker Compose remains local-only and must not be used as the production deployment mechanism on Vercel.

Synchronous generation is acceptable for the MVP while OpenRouter requests fit within Vercel Hobby function duration. If generation regularly times out or approaches platform limits, use the existing `generation_jobs` structure as the migration path to a future async polling/queue/worker phase instead of adding deployment-specific business logic.

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
| `FULL_PAGE_GENERATION_COST` | Full page generation coin cost | `20` |
| `SCENE_REGENERATION_COST` | Scene regeneration coin cost | `4` |
| `STARTER_COINS` | Starter wallet coin amount | `100` |
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
| `OPENROUTER_API_KEY` | Server-side OpenRouter API key for generation/text | unset |
| `OPENROUTER_SITE_URL` | Referer sent to OpenRouter | `https://comicly.ai` |
| `OPENROUTER_APP_NAME` | App title sent to OpenRouter | `comicly.ai` |
| `OPENROUTER_DEFAULT_IMAGE_MODEL` | Default image model when request omits `model_id` | `bytedance-seed/seedream-4.5` |
| `OPENROUTER_DEFAULT_TEXT_MODEL` | Default AI text model | `google/gemini-2.5-flash` |
| `OPENROUTER_ALLOWED_IMAGE_MODELS` | Comma-separated image model allow-list | configured list |
| `OPENROUTER_IMAGE_ASPECT_RATIO` | Image aspect ratio sent to OpenRouter | `1:1` |
| `OPENROUTER_REQUEST_TIMEOUT_SECONDS` | OpenRouter request timeout | `60` |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob read-write token | unset |
| `SECURITY_HEADERS_ENABLED` | Enable baseline API security headers | `true` |
| `RATE_LIMIT_ENABLED` | Enable in-process sensitive-route rate limiting | `true` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window size in seconds | `60` |
| `RATE_LIMIT_MAX_REQUESTS` | Max sensitive requests per client/window | `60` |

For Vercel/Neon production:

- `DATABASE_URL` should be the Neon pooled connection URL converted to the async SQLAlchemy driver form, for example `postgresql+asyncpg://...`.
- `MIGRATION_DATABASE_URL` should be the Neon direct non-pooled URL for Alembic when available.
- `SESSION_SECRET`, OAuth secrets, `OPENROUTER_API_KEY`, and `BLOB_READ_WRITE_TOKEN` should be configured through environment variables, not committed files.
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

OpenRouter and Blob secrets are intentionally optional at import/startup time so health checks, tests, and non-generation APIs can run without live provider credentials. Live generation and AI text calls require `OPENROUTER_API_KEY`; live image persistence requires `BLOB_READ_WRITE_TOKEN`.

## Security Controls

The backend adds baseline security headers to API responses:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY`
- `Permissions-Policy` disabling camera, microphone, geolocation, and payment APIs
- `Strict-Transport-Security` only when running in production with secure cookies enabled

Sensitive routes also have simple in-process rate limiting:

- OAuth routes under `/api/v1/auth/...`
- profile writes and logout under `/api/v1/me`
- `POST /api/v1/ai-text`
- `POST /api/v1/generations`
- write operations under `/api/v1/comics...`

Exceeded limits return HTTP `429` with error code `RATE_LIMITED`. The limiter is portable and requires no Redis or Vercel-only service, but it is best-effort in serverless because each function instance has its own memory. Use Vercel Firewall or another shared rate-limit layer later if abuse patterns require global enforcement.

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

If a user cannot cover a debit, the service returns `INSUFFICIENT_COINS` with HTTP status `409` and does not create a debit row. If OpenRouter generation or Blob persistence fails after a debit, the generation service marks the job/page failed and records one idempotent refund transaction rather than silently editing the original debit.

## Generation Pipeline

Phase 6 generation is backend-owned and API-only. The static frontend is not changed until Phase 7.

The synchronous MVP flow is:

1. Authenticated client sends `POST /api/v1/generations` with `Idempotency-Key`.
2. Backend validates `model_id` against `OPENROUTER_ALLOWED_IMAGE_MODELS`; disallowed models return `MODEL_NOT_ALLOWED`.
3. Backend creates a `generation_jobs` audit record and prepares an owned comic page.
4. Backend debits `FULL_PAGE_GENERATION_COST` through the wallet ledger.
5. Backend calls OpenRouter with server-side credentials.
6. Backend uploads the generated image to Vercel Blob.
7. Backend marks the job/page `succeeded` and returns job, page, updated balance, and Blob `image_url`.

If OpenRouter or Blob fails after debit, the backend marks the job/page `failed` and records one idempotent refund. Repeating the same `Idempotency-Key` replays the completed job result and does not double-charge or re-call external services.

This phase deliberately does not add a queue, worker, webhook, or polling endpoint. If generation regularly exceeds Vercel Function limits, the existing `generation_jobs` table is ready to support a later async polling/queue implementation.

## Private Comic Persistence

Comic persistence is backend-owned and API-only in Phase 5. The frontend has not been changed yet.

Stored comic draft metadata includes:

- `title`
- `story`
- `characters`
- `style`
- `tone`
- `selected_model`
- `status`

Stored scene fields include:

- `position`
- `title`
- `description`
- `dialogue`
- `caption`

Stored page fields include:

- `page_number`
- `status`
- `model`
- `coin_cost`
- `image_url`
- `storage_key`
- `width`
- `height`
- `scene_id`
- `generated_at`

Comics are soft-archived with status `archived`; list responses hide archived comics unless `include_archived=true` is requested. Scene and page replacement endpoints use stable ordering by `position` and `page_number`. Phase 5 does not call OpenRouter, debit coins, upload images, or integrate the existing static creator UI; those belong to later phases.

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
