# Comicly Deployment Runbook

This runbook covers the MVP Vercel-first deployment path for the static frontend and standalone FastAPI backend.

## Architecture

- Frontend Vercel project: repository root, domain `comicly-ai.ru`.
- Backend Vercel project: `backend/` root, served through frontend rewrites under `comicly-ai.ru/api/v1/...`.
- Production database: managed Postgres through Vercel Marketplace, preferably Neon.
- Production object storage: Vercel Blob.
- Local database: Docker Compose Postgres from `backend/docker-compose.yml`.
- Docker Compose is not used for production on Vercel.

## Local Setup

From the backend directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
docker compose up -d postgres
python -m alembic upgrade head
python scripts/seed_coin_packages.py
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

From the repository root, the static frontend can still be served locally:

```powershell
npm start
```

Quality gates:

```powershell
cd backend
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Root/static checks:

```powershell
node --test tests/phase7-static-contract.test.mjs tests/phase8-deploy-config.test.mjs
npm run build:frontend
```

## Production Environment

Set production secrets in Vercel project environment variables. Do not commit real values.

Backend production variables:

- `APP_ENV=production`
- `DATABASE_URL` - Neon pooled runtime URL converted to `postgresql+asyncpg://...`
- `MIGRATION_DATABASE_URL` - Neon direct non-pooled URL for Alembic
- `CORS_ORIGINS=https://comicly-ai.ru`
- `SESSION_SECRET` - long random secret, never the local placeholder
- `FRONTEND_CREATOR_URL=https://comicly-ai.ru/create.html`
- `OAUTH_CALLBACK_BASE_URL=https://comicly-ai.ru`
- `SESSION_COOKIE_DOMAIN=.comicly-ai.ru`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `YANDEX_CLIENT_ID`
- `YANDEX_CLIENT_SECRET`
- `OPENROUTER_API_KEY`
- `OPENROUTER_SITE_URL=https://comicly-ai.ru`
- `OPENROUTER_APP_NAME=comicly-ai.ru`
- `BLOB_READ_WRITE_TOKEN`
- `YOOKASSA_SHOP_ID`
- `YOOKASSA_API_KEY`
- `YOOKASSA_RETURN_URL=https://comicly-ai.ru/pricing.html?payment=return`
- `SECURITY_HEADERS_ENABLED=true`
- `RATE_LIMIT_ENABLED=true`

Generation pricing and model variables may keep the defaults from `backend/.env.example` unless product pricing changes.
Payment packages are seeded through `python scripts/seed_coin_packages.py`; rerun it after deploying payment pricing changes so the production database has the active RUB packages.

## Database

1. Add a Postgres provider from Vercel Marketplace, preferably Neon.
2. Attach the database integration to the backend Vercel project.
3. Use the pooled connection string for `DATABASE_URL`.
4. Use a direct connection string for `MIGRATION_DATABASE_URL` when running Alembic.
5. Run migrations:

```powershell
cd backend
python -m alembic upgrade head
python scripts/seed_coin_packages.py
```

If migrations are run from a local machine, ensure the environment has production `MIGRATION_DATABASE_URL` and not only the pooled runtime URL.

## Blob Storage

Create or attach Vercel Blob storage to the backend project and set `BLOB_READ_WRITE_TOKEN`.

Generated images should be delivered by their Blob URL. Do not proxy generated image bytes through the FastAPI response and do not return provider base64 payloads.

## OAuth Providers

Register these production callback URLs:

- Google: `https://comicly-ai.ru/api/v1/auth/google/callback`
- Yandex: `https://comicly-ai.ru/api/v1/auth/yandex/callback`

Local callback URLs:

- Google: `http://localhost:8000/api/v1/auth/google/callback`
- Yandex: `http://localhost:8000/api/v1/auth/yandex/callback`

After login, both providers should redirect back to `https://comicly-ai.ru/create.html` through `FRONTEND_CREATOR_URL`.

## YooKassa

In YooKassa, configure the payment notification URL:

```text
https://comicly-ai.ru/api/v1/payments/webhook
```

The backend verifies webhook source IP ranges in production by default and then fetches the payment from YooKassa before granting coins. Keep `YOOKASSA_WEBHOOK_IP_CHECK_ENABLED=true` in production unless an upstream trusted proxy enforces the same allow-list.

Until `comicly-ai.ru` is attached and healthy, use the working Vercel aliases in YooKassa settings:

- Return URL: `https://comicly-ai.vercel.app/pricing.html?payment=return`
- Webhook URL: `https://comicly-backend.vercel.app/api/v1/payments/webhook`

## Vercel Projects

Frontend project:

- Vercel project name: `comicly-frontend`
- Root directory: repository root
- Build command: `npm run build:frontend`
- Output directory: `dist`
- Domain: `comicly-ai.ru`

Backend project:

- Root directory: `backend`
- Runtime: Python 3.12
- Entry point: `api/index.py`, which imports the FastAPI app from `app/main.py`
- `backend/vercel.json` rewrites all paths to `/api/index` so unprefixed routes like `/health` and `/ready` are handled by FastAPI.
- Public API route: `https://comicly-ai.ru/api/v1/...`
- Functions max duration: set to 300 seconds in the Vercel project settings/dashboard where supported

Vercel Python runtime is Beta. Keep the backend portable so it can move to Render, Railway, Fly.io, or a container service without rewriting business logic.

If a backend deployment is `READY` but `/health` returns Vercel `NOT_FOUND`, check that the project has the `api/index.py` function entrypoint and the rewrite rule above. A generic static/Other project can otherwise deploy successfully without creating a Python function.

Preview deployments may be protected by Vercel Authentication. If a direct browser or smoke helper request returns the Vercel "Authentication Required" HTML page, use the authenticated CLI path instead:

```powershell
npx vercel curl /health --deployment <backend-preview-url> --cwd backend
```

The root frontend project must be a normal static Vercel project using `vercel.json` with `buildCommand` and `outputDirectory`. The first project named `comicly.ai` was accidentally created with Vercel's Services framework preset and fails with `No services configured. Add experimentalServices to vercel.json.` Do not use that project for the static frontend.

The working frontend deployment uses a separate Vercel project named `comicly-frontend`.

### Repeat Frontend Deploy

From the repository root:

```powershell
npx vercel link --yes --project comicly-frontend --scope d1sneys-projects
npm run build:frontend
npx vercel deploy --prod --yes --no-color
```

Successful deployment evidence from 2026-04-29:

- Project: `comicly-frontend`
- Production alias: `https://comicly-frontend.vercel.app`
- Deployment URL: `https://comicly-frontend-m3kf92a6s-d1sneys-projects.vercel.app`
- Inspect URL: `https://vercel.com/d1sneys-projects/comicly-frontend/8CdNwe7N2sQamiGa1KVgbGFLC2TX`

After deploy, verify:

```powershell
curl.exe -L -I https://comicly-frontend.vercel.app/
curl.exe -L -I https://comicly-frontend.vercel.app/create.html
```

`/create.html` may redirect to `/create` with HTTP 308 because Vercel clean URLs are enabled for static output; the final response should be HTTP 200.

To launch the real domain, attach `comicly-ai.ru` to the `comicly-frontend` project in the Vercel dashboard and remove old domains from deprecated projects if necessary.

## Smoke Checks

Local example:

```powershell
python backend/scripts/smoke_production.py --api-base-url http://localhost:8000 --frontend-url http://localhost:3000 --skip-ready
```

Production example:

```powershell
python backend/scripts/smoke_production.py --api-base-url https://comicly-ai.ru --frontend-url https://comicly-ai.ru
```

The smoke helper checks public reachability, `/health`, `/ready` unless skipped, and OAuth login route reachability. It does not claim that live OAuth callback or live generation succeeded.

Manual production checks:

- Google login starts, callback succeeds, session cookie is set, and user lands on `/create.html`.
- Yandex login starts, callback succeeds, session cookie is set, and user lands on `/create.html`.
- Authenticated creator loads profile/balance from backend.
- A generation request succeeds, spends coins once, stores the image in Blob, and returns an `image_url`.
- Insufficient coins and provider failures show normal frontend errors.

## Rollback And Fallback

If backend deploy fails because of Vercel Python runtime limitations, keep the same FastAPI app and deploy `backend/` to Render/Railway/Fly.io. Required environment variables and migration commands remain the same.

If synchronous generation frequently exceeds function duration, do not patch around it in deployment config. Use a future async job/polling/worker phase built on the existing `generation_jobs` schema.
