# Phase 2: Data And Payment Foundation - Research

**Researched:** 2026-04-26
**Phase:** 2 - Data And Payment Foundation
**Status:** Ready for planning

## Research Summary

Phase 2 should turn the Phase 1 database scaffold into the durable schema foundation for the production backend while staying inside `backend/`.

The phase should not implement OAuth login, wallet debit/refund operations, real checkout/webhooks, OpenRouter generation, object storage, or frontend integration. It should create the tables, constraints, migration path, seed data, configuration, and minimal package catalog surface that later phases will depend on.

## Deployment Research

Vercel-first remains viable for MVP if the backend is serverless-friendly:

- Frontend deploys separately to Vercel static hosting on `comicly.ai` / `www.comicly.ai`.
- Backend deploys as a separate Vercel project rooted at `backend/`.
- Production API domain is `api.comicly.ai`.
- Production DB is managed Postgres through Vercel Marketplace, preferably Neon.
- Runtime app uses Neon pooled connection URL via `DATABASE_URL`.
- Alembic migrations may need a direct non-pooled URL via `DATABASE_DIRECT_URL` or `MIGRATION_DATABASE_URL`.
- Local development uses Docker Compose Postgres.

Planning implication: runtime SQLAlchemy engine should stay conservative for serverless, and Alembic should explicitly prefer the direct migration URL when present.

## Schema Approach

Use SQLAlchemy 2 typed declarative models under `backend/app/models/`.

Recommended grouping:

- `user.py`: users, provider identities, profiles, sessions.
- `wallet.py`: wallets, wallet transactions.
- `comic.py`: comics, scenes, pages.
- `generation.py`: generation jobs.
- `payment.py`: coin packages, payment placeholders.
- `__init__.py`: imports all models so Alembic metadata sees them.

Use UUID primary keys where possible for externally-referenced objects. Use timezone-aware timestamps. Keep status/type values as Python string enums mapped to database enums or validated strings; planner/executor can choose the simplest Alembic-friendly approach.

## Constraint Priorities

Phase 2 must prevent obvious corruption before business logic exists:

- unique provider identity by `(provider, provider_user_id)`;
- unique session token/hash identifiers where applicable;
- one wallet per user;
- non-negative wallet balance;
- wallet transaction idempotency key uniqueness;
- coin package uniqueness by coin amount or stable code;
- payment provider/idempotency uniqueness where nullable behavior is safe;
- comic/page/scene ownership through foreign keys and cascades that avoid orphaned private data;
- generation job status and entity references that can support sync MVP and future queue polling.

## Seed And Runtime Config

Seed active coin packages:

- 100 coins
- 500 coins
- 1000 coins

Runtime pricing config should be centralized. At minimum:

- full page generation cost: 20 coins;
- scene regeneration cost: 4 coins;
- starter coins: env-configurable.

This can start in `Settings` and be mirrored in tests/docs. Do not scatter prices through route handlers or frontend code.

## API Surface

Phase 2 may add a minimal `/api/v1/coin-packages` read endpoint because roadmap success criteria require product code to fetch the active package catalog. It should not require auth yet unless the planner deliberately chooses a placeholder dependency. The route should only expose active package catalog data and not create payments.

## Testing Strategy

Use the existing Pytest/Ruff setup.

Recommended tests:

- model metadata includes all required tables;
- Alembic can create schema from a clean database;
- constraints reject representative duplicates/invalid values;
- seed command or migration creates 100/500/1000 active packages idempotently;
- pricing settings load defaults and env overrides;
- catalog endpoint returns active packages only;
- tests do not depend on production Neon.

Local integration tests can use Docker Postgres if available, but plans should keep fast tests available through metadata/unit checks and a clear command for migration verification.

## Validation Architecture

Dimension 1 - Scope:

- Only `backend/` source plus `.planning/` docs should be modified.
- No frontend/root runtime files.
- No production deployment execution.

Dimension 2 - Requirement Coverage:

- DATA-01: Alembic migration path creates all production tables from clean checkout.
- DATA-02: SQLAlchemy models cover users, identities, profiles, sessions, wallets, wallet transactions, comics, scenes, pages, generation jobs, coin packages, and payments.
- DATA-03: database constraints cover duplicate identities/idempotency, invalid balances, and ownership relationships.
- DATA-04: seed path creates active 100/500/1000 coin packages.
- DATA-05: runtime config centralizes generation costs and starter coins.
- PAY-01: backend exposes active coin package catalog.
- PAY-02: payment placeholder schema includes status, user, package, amount, currency, external provider fields.
- PAY-03: payment schema supports future webhook/provider idempotency.

Dimension 3 - Verification:

- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format --check .`
- Alembic migration upgrade against local Postgres or a documented integration command.
- `docker compose` remains local-only.

Dimension 4 - Deferral Integrity:

- No OAuth callbacks.
- No wallet debit/credit service behavior.
- No real checkout/webhook fulfillment.
- No OpenRouter calls.
- No frontend integration.

## References

- `backend/BACKEND_TZ.md`
- `.planning/phases/02-data-and-payment-foundation/02-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/01-backend-foundation-and-static-safety/01-CONTEXT.md`
- Vercel FastAPI docs: `https://vercel.com/docs/frameworks/backend/fastapi`
- Vercel Python runtime docs: `https://vercel.com/docs/functions/runtimes/python`
- Vercel function limits: `https://vercel.com/docs/functions/limitations`
- Vercel/Neon marketplace docs: `https://vercel.com/marketplace/neon`
- Vercel connection pooling guide: `https://vercel.com/kb/guide/connection-pooling-with-functions`
- Neon pricing: `https://neon.com/pricing`

---

## RESEARCH COMPLETE

Lightweight research artifact written for Phase 2. Ready for planning.
