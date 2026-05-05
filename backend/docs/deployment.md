# Comicly VPS Deployment Runbook

This branch targets a classic VPS deployment with Caddy, Docker Compose, external managed PostgreSQL, and S3-compatible object storage.

## Architecture

- `docker-compose.yml` runs Caddy and the FastAPI backend container.
- `deploy/caddy/Caddyfile` serves `dist/` as the static frontend.
- Caddy proxies `/api/v1/*`, `/health`, and `/ready` to `backend-api:8000`.
- PostgreSQL is external managed Postgres.
- Generated images are stored in S3-compatible object storage.
- Caddy obtains and renews HTTPS certificates automatically.

## Required Services

- VPS with Docker Engine and Docker Compose plugin.
- DNS A/AAAA records for `comicly-ai.ru` and optionally `www.comicly-ai.ru` pointing to the VPS.
- Managed PostgreSQL with an async SQLAlchemy URL.
- S3-compatible bucket with a public base URL or CDN/custom domain.
- OAuth provider callbacks for the production domain.

## Initial Setup

```bash
git clone <repo-url> comicly.ai
cd comicly.ai
cp backend/.env.example backend/.env
cp .env.example .env
```

Edit `backend/.env` with real production values:

- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `SESSION_SECRET`
- Google/Yandex OAuth credentials
- `OPENROUTER_API_KEY`
- S3 endpoint, bucket, keys, and public base URL
- YooKassa credentials

Edit root `.env` for Caddy/frontend build variables:

```dotenv
COMICLY_SITE_ADDRESS=comicly-ai.ru, www.comicly-ai.ru
ACME_EMAIL=admin@comicly-ai.ru
COMICLY_API_BASE_URL=
```

Leave `COMICLY_API_BASE_URL` empty when Caddy serves frontend and backend on the same origin.

## Build Frontend

```bash
npm install
npm run build:frontend
```

The build creates `dist/` and writes `dist/scripts/runtime-config.js`.

If the backend is hosted on a separate API domain, build with:

```bash
COMICLY_API_BASE_URL="https://api.comicly-ai.ru" npm run build:frontend
```

## Start Runtime

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
docker compose logs -f caddy backend-api
```

## Migrations And Seed Data

```bash
docker compose run --rm backend-api python -m alembic upgrade head
docker compose run --rm backend-api python scripts/seed_coin_packages.py
```

## OAuth Provider Callbacks

Register these production callbacks:

- `https://comicly-ai.ru/api/v1/auth/google/callback`
- `https://comicly-ai.ru/api/v1/auth/yandex/callback`

The backend redirects users back to `FRONTEND_CREATOR_URL`, normally `https://comicly-ai.ru/create.html`.

## YooKassa

Configure the webhook URL:

```text
https://comicly-ai.ru/api/v1/payments/webhook
```

Set the return URL:

```text
https://comicly-ai.ru/pricing.html?payment=return
```

## Smoke Checks

```bash
curl -I https://comicly-ai.ru/
curl https://comicly-ai.ru/health
curl https://comicly-ai.ru/ready
```

Manual checks:

- Google login starts and returns to `/create.html`.
- Yandex login starts and returns to `/create.html`.
- Creator loads backend profile and wallet.
- A generation request spends coins once and stores the image in S3.
- YooKassa webhook reaches `/api/v1/payments/webhook`.

## Rollback

```bash
git checkout <previous-commit>
npm run build:frontend
docker compose up -d --build
```
