# Comicly Deployment Runbook

This runbook covers the MVP Vercel-first deployment path for the static frontend and standalone FastAPI backend.

## Architecture

- Frontend Vercel project: repository root, domain `comicly.ai` and `www.comicly.ai`.
- Backend Vercel project: `backend/` root, domain `api.comicly.ai`.
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
- `CORS_ORIGINS=https://comicly.ai,https://www.comicly.ai`
- `SESSION_SECRET` - long random secret, never the local placeholder
- `FRONTEND_CREATOR_URL=https://comicly.ai/create.html`
- `SESSION_COOKIE_DOMAIN=.comicly.ai`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=lax`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `YANDEX_CLIENT_ID`
- `YANDEX_CLIENT_SECRET`
- `OPENROUTER_API_KEY`
- `OPENROUTER_SITE_URL=https://comicly.ai`
- `OPENROUTER_APP_NAME=comicly.ai`
- `BLOB_READ_WRITE_TOKEN`
- `SECURITY_HEADERS_ENABLED=true`
- `RATE_LIMIT_ENABLED=true`

Generation pricing and model variables may keep the defaults from `backend/.env.example` unless product pricing changes.

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

- Google: `https://api.comicly.ai/api/v1/auth/google/callback`
- Yandex: `https://api.comicly.ai/api/v1/auth/yandex/callback`

Local callback URLs:

- Google: `http://localhost:8000/api/v1/auth/google/callback`
- Yandex: `http://localhost:8000/api/v1/auth/yandex/callback`

After login, both providers should redirect back to `https://comicly.ai/create.html` through `FRONTEND_CREATOR_URL`.

## Vercel Projects

Frontend project:

- Vercel project name: `comicly-frontend`
- Root directory: repository root
- Build command: `npm run build:frontend`
- Output directory: `dist`
- Domains: `comicly.ai`, `www.comicly.ai`

Backend project:

- Root directory: `backend`
- Runtime: Python 3.12
- Entry point: `index.py`, which imports the FastAPI app from `app/main.py`
- Domain: `api.comicly.ai`
- Functions max duration: set to 300 seconds in the Vercel project settings/dashboard where supported

Vercel Python runtime is Beta. Keep the backend portable so it can move to Render, Railway, Fly.io, or a container service without rewriting business logic.

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

To launch the real domain, attach `comicly.ai` and `www.comicly.ai` to the `comicly-frontend` project in the Vercel dashboard and remove those domains from the old Services-mode `comicly.ai` project if necessary.

## Smoke Checks

Local example:

```powershell
python backend/scripts/smoke_production.py --api-base-url http://localhost:8000 --frontend-url http://localhost:3000 --skip-ready
```

Production example:

```powershell
python backend/scripts/smoke_production.py --api-base-url https://api.comicly.ai --frontend-url https://comicly.ai
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
