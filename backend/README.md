# Comicly Backend

FastAPI backend for Comicly.ai. In this branch the production target is VPS + Caddy + Docker Compose, with external managed PostgreSQL and S3-compatible object storage.

## Local Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Run the API locally:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health endpoints:

- `GET /health`
- `GET /ready`

Business APIs are under `/api/v1/`.

## API Surface

- `GET /api/v1/auth/google/login`
- `GET /api/v1/auth/google/callback`
- `GET /api/v1/auth/yandex/login`
- `GET /api/v1/auth/yandex/callback`
- `GET /api/v1/me`
- `PATCH /api/v1/me`
- `POST /api/v1/me/logout`
- `GET /api/v1/wallet`
- `GET /api/v1/coin-packages`
- `POST /api/v1/comics`
- `GET /api/v1/comics`
- `GET /api/v1/comics/{comic_id}`
- `PATCH /api/v1/comics/{comic_id}`
- `DELETE /api/v1/comics/{comic_id}`
- `PUT /api/v1/comics/{comic_id}/scenes`
- `PUT /api/v1/comics/{comic_id}/pages`
- `POST /api/v1/ai-text`
- `POST /api/v1/generations`
- `POST /api/v1/payments`
- `POST /api/v1/payments/{payment_id}/refresh`
- `POST /api/v1/payments/webhook`

## Environment

Copy `backend/.env.example` to `backend/.env` and set real values.

Important production variables:

- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `CORS_ORIGINS`
- `SESSION_SECRET`
- `FRONTEND_CREATOR_URL`
- `OAUTH_CALLBACK_BASE_URL`
- `SESSION_COOKIE_DOMAIN`
- `SESSION_COOKIE_SECURE=true`
- Google/Yandex OAuth credentials
- `OPENROUTER_API_KEY`
- S3 variables: `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_PUBLIC_BASE_URL`
- YooKassa credentials

Generated images are always persisted through S3-compatible object storage. The generation response returns durable metadata and `image_url`; it must not return provider base64 image data.

## Wallet Ledger

Wallet balance is authoritative in PostgreSQL. Browser-sent balances, owner ids, generation costs, and payment state are not trusted.

Every balance change creates a `wallet_transactions` row. Billable generation requires an `Idempotency-Key`, debits before provider calls, and refunds once if OpenRouter or S3 storage fails after debit.

Default costs:

- full page generation: `20`
- scene regeneration: `4`

## Generation Pipeline

1. Authenticated client sends `POST /api/v1/generations` with `Idempotency-Key`.
2. Backend validates the model allow-list.
3. Backend creates a `generation_jobs` audit record and prepares an owned comic page.
4. Backend debits coins through the wallet ledger.
5. Backend calls OpenRouter.
6. Backend uploads the generated image to S3-compatible storage.
7. Backend marks the job/page `succeeded` and returns job, page, updated balance, and durable `image_url`.

Repeating the same `Idempotency-Key` replays the completed result and does not double-charge or re-call external services.

## Deployment

See `backend/docs/deployment.md`.

Root production files:

- `docker-compose.yml`
- `deploy/caddy/Caddyfile`
- `.env.example`
- `backend/.env.example`

## Quality Gates

Run from `backend/`:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Root/static checks:

```powershell
npm.cmd run test:phase7
npm.cmd run test:phase8
npm.cmd run build:frontend
docker compose config
```

## Migrations

Alembic prefers `MIGRATION_DATABASE_URL`, then `DATABASE_DIRECT_URL`, then `DATABASE_URL`.

```powershell
cd backend
python -m alembic upgrade head
python scripts/seed_coin_packages.py
```
