# Phase 8: Deployment And Operations - Research

**Date:** 2026-04-29
**Status:** Complete

## Research Question

What does Phase 8 need to plan well so the current static frontend and FastAPI backend can be configured, deployed, documented, smoke-tested, and minimally protected for a Vercel-first MVP?

## Current Constraints

- Backend remains API-only FastAPI under `backend/`.
- Frontend is static HTML/CSS/JS at repo root.
- Production target is Vercel-first:
  - frontend: `comicly.ai` and `www.comicly.ai`;
  - backend: `api.comicly.ai`.
- Production Postgres should use Vercel Marketplace external Postgres, preferably Neon.
- Runtime DB URL should be pooled `DATABASE_URL`; migrations should use direct `MIGRATION_DATABASE_URL` or `DATABASE_DIRECT_URL`.
- Generated images are stored in Vercel Blob and returned as `image_url`, not base64.
- Docker Compose remains local-only.
- Real secrets must not be committed.

## Official Platform Findings

- Vercel Python runtime is available on all plans but is marked Beta. It supports ASGI/WSGI apps and FastAPI, and Vercel detects Python dependencies from `requirements.txt`, `pyproject.toml`, or `Pipfile`.
  - Source: https://vercel.com/docs/functions/runtimes/python
- Vercel Python default version is 3.12 when not otherwise configured. The project already chose Python 3.12, so adding a project-local version file/config is aligned.
  - Source: https://vercel.com/docs/functions/runtimes/python
- With Fluid Compute, Vercel Hobby functions can run up to 300 seconds. This is enough for MVP synchronous generation only if OpenRouter image generation reliably fits within that budget.
  - Source: https://vercel.com/docs/functions/configuring-functions/duration
- Vercel Functions have request/response and bundle limits. The generation API must keep returning durable URLs rather than large base64 payloads.
  - Source: https://vercel.com/docs/functions/limitations
- Vercel Postgres is no longer the native product for new projects; Vercel recommends connecting external Postgres databases through Marketplace integrations, and notes Neon migration/integration context.
  - Source: https://vercel.com/docs/postgres
- Vercel Blob is free for Hobby users within usage limits, but exceeding limits blocks access until the period resets. Public blob delivery is cheaper than proxying through a Function.
  - Source: https://vercel.com/docs/vercel-blob/usage-and-pricing

## Codebase Findings

- `backend/app/main.py` already exposes `app = create_app()`, which is compatible with the Vercel Python runtime expectation of a top-level `app` in a recognized entrypoint.
- `backend/app/core/config.py` already has most production env settings:
  - DB: `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `DATABASE_DIRECT_URL`
  - CORS/cookies: `CORS_ORIGINS`, `SESSION_COOKIE_DOMAIN`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`
  - OAuth: Google/Yandex client IDs/secrets
  - Providers: `OPENROUTER_API_KEY`, `BLOB_READ_WRITE_TOKEN`
- `backend/.env.example` and `backend/README.md` already document many local and provider settings, but Phase 8 needs a fuller local/production deployment runbook.
- Root `.env.example` is legacy/garbled text and OpenRouter-only. Phase 8 should either make it safe/current or move authoritative production env docs to backend/deployment docs.
- Frontend production API base is already `https://api.comicly.ai` in `scripts/creator.js`.
- No Vercel config is present for either frontend or backend.
- Root static deployment must avoid exposing repo-root private files. A build step that copies only public frontend files into a static output directory is safer than deploying the repository root as-is.

## Recommended Planning Shape

### Plan 01 - Vercel Deployment Config And Static Safety

Create minimal Vercel-compatible deployment config:
- root frontend project builds a public output directory from an explicit allow-list of static files;
- backend project rooted at `backend/` has Python 3.12/Vercel config and FastAPI routing;
- config includes max duration where supported and keeps Docker Compose local-only.

### Plan 02 - Backend Security Headers And Rate Limiting

Implement portable backend controls:
- security headers middleware;
- simple in-process rate limiting for sensitive endpoints;
- tests for headers, limits, and health/readiness behavior.

### Plan 03 - Env, Local Ops, Production Runbook, Smoke Tooling

Make operation repeatable:
- update `.env.example` files without secrets;
- document local install/migrations/tests/startup;
- document production DB, Blob, OAuth, cookies, CORS, domains;
- add a small smoke/checklist artifact or script that can verify local/production surfaces.

### Plan 04 - Deployment Attempt And Final Verification

Attempt real Vercel setup/deploy/smoke when credentials are available:
- use Vercel tools/CLI where possible;
- run backend gates and static contract tests;
- smoke deployed URLs where available;
- if blocked by access/secrets/domains, write exact manual checklist and residual gaps.

## Validation Architecture

Phase 8 should validate with layered checks:

- Config/docs contract checks:
  - no committed secret values;
  - `.env.example` names match `Settings` fields;
  - Vercel/static output config exists and does not expose private paths.
- Backend automated checks:
  - `python -m pytest`
  - `python -m ruff check .`
  - `python -m ruff format --check .`
- Root/static checks:
  - `node --test tests/phase7-static-contract.test.mjs`
  - frontend build/static output test if a build script is added.
- Deployment smoke:
  - `/health`
  - `/ready`
  - frontend landing public
  - creator auth overlay/login route links
  - CORS/cookie shape
- Manual/live-provider checks:
  - Google OAuth callback on `api.comicly.ai`
  - Yandex OAuth callback on `api.comicly.ai`
  - real OpenRouter generation with Blob URL result

## Risks

- Vercel Python runtime is Beta, so the backend must stay portable and should not absorb Vercel-only business logic.
- Synchronous OpenRouter image generation may approach or exceed function duration under load/provider slowness. Phase 8 should document the async migration trigger but not implement queue/worker.
- In-process rate limiting is best-effort in serverless because instances are ephemeral and not globally shared. It is still useful as MVP abuse friction, but not a full WAF.
- Real production OAuth/generation checks depend on secrets, domain DNS, provider console callback configuration, and Vercel project access.

## Research Complete

The phase can be planned with four sequential plans: deployment config, security controls, operations documentation/smoke tooling, and deploy verification.
