# Phase 2: Data And Payment Foundation - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 creates the durable data and payment-preparation foundation for the standalone FastAPI backend in `backend/`.

In scope: SQLAlchemy models, Alembic migrations, database constraints, seed data for coin packages, runtime pricing configuration, payment placeholder schema, and connection/config patterns that work for both local Docker Postgres and production Neon on Vercel.

Out of scope for Phase 2: OAuth implementation, wallet debit/credit business operations, real payment checkout/webhooks, OpenRouter generation execution, frontend integration, and production deployment execution. Those remain later phases.

</domain>

<decisions>
## Implementation Decisions

### Deployment Target And Portability
- **D-01:** MVP deployment target is Vercel-first because the user is already signed into Vercel skills/tools in Codex and wants the setup that Codex can configure most independently.
- **D-02:** Frontend deploys to Vercel on `comicly.ai` and `www.comicly.ai`.
- **D-03:** Backend remains a standalone API-only FastAPI service inside `backend/`.
- **D-04:** Backend production API domain should be `api.comicly.ai`.
- **D-05:** Use a separate Vercel project rooted at `backend/` for the backend API unless planning discovers a simpler stable Vercel-native option. Do not use Vercel Services unless it is generally available and clearly stable.
- **D-06:** Keep backend portable: business logic must remain ordinary FastAPI/SQLAlchemy code so it can move to Render, Railway, Fly.io, or container hosting without rewriting core behavior.
- **D-07:** Docker Compose remains local-development only. Do not plan Docker Compose as Vercel production deployment.

### Production Database
- **D-08:** Production Postgres should be managed Postgres through Vercel Marketplace, preferably Neon, with a free-first/Hobby-friendly setup.
- **D-09:** Runtime app should use Neon pooled connection URL as `DATABASE_URL`, because Vercel Functions are serverless and can create many short-lived connections.
- **D-10:** Alembic migrations may use a direct non-pooled Neon URL via a separate env var such as `DATABASE_DIRECT_URL` or `MIGRATION_DATABASE_URL`; planner should choose the clearest name and document it.
- **D-11:** Local development continues to use PostgreSQL from `backend/docker-compose.yml`.
- **D-12:** Phase 2 should configure SQLAlchemy/Alembic so local Docker Postgres and production Neon share one schema/migration path.

### Phase 2 Schema Shape
- **D-13:** Phase 2 should include tables required by later phases: users, OAuth provider identities, profiles, sessions, wallets, wallet transactions, comics, comic scenes, comic pages, generation jobs, coin packages, and payment placeholders.
- **D-14:** Generation jobs should be modeled now with status fields and enough metadata to support later queue/status polling, even though MVP generation may start synchronously.
- **D-15:** Payment tables are placeholders only: package catalog, payment status, user/package references, amount/currency, provider fields, and future webhook idempotency support.
- **D-16:** Real checkout, provider webhooks, and purchased-coin fulfillment stay out of Phase 2.

### MVP Generation And Vercel Limits
- **D-17:** MVP can use synchronous backend calls to OpenRouter/model APIs within Vercel Hobby/Function duration limits.
- **D-18:** Schema should preserve an upgrade path from synchronous generation to jobs/status polling/queue without redesigning comic/page/wallet tables.
- **D-19:** Do not build an enterprise queue pipeline in Phase 2; model the data foundation only.

### Env And Secrets
- **D-20:** Production secrets/settings must come from environment variables, not committed files.
- **D-21:** Required/future env names should include `DATABASE_URL`, direct migration DB URL, `CORS_ORIGINS`, `SESSION_SECRET`, OAuth client IDs/secrets, `OPENROUTER_API_KEY`, storage vars, pricing vars, and `STARTER_COINS`.
- **D-22:** Phase 2 should expand backend env docs only as needed for schema/migrations/config. Avoid frontend/root changes.

### Roadmap Handling
- **D-23:** Do not add a new deployment phase by default; Phase 8 already covers Deployment And Operations.
- **D-24:** If an early deployment proof becomes useful before Phase 8, it can be inserted later as a small Phase 2.1 Vercel/Neon deployment spike.

### Cost And Workflow Constraints
- **D-25:** Work budget/token-efficiently: avoid unnecessary subagents, avoid deep research unless a planning blocker appears, and prefer official docs plus existing project artifacts.
- **D-26:** Phase 2 planning should be minimal but complete for MVP. Do not inflate docs or add extra phases unless necessary.
- **D-27:** Do not execute Phase 2 until the user explicitly invokes execution.

### the agent's Discretion
- Exact names for SQLAlchemy models and tables, as long as they are clear and stable.
- Exact direct migration DB env var name, choosing the clearest convention for Alembic + Neon.
- Whether pricing config starts as env-backed settings, DB-backed config, or a small hybrid, as long as costs are not scattered across frontend/backend code.
- Whether seed command is an Alembic data migration, a small script, or an app CLI, as long as it is simple and testable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backend Requirements
- `backend/BACKEND_TZ.md` - primary source of truth for backend product, auth, wallet, comic history, payment-prep, deployment, security, and acceptance requirements.

### Phase 2 Scope
- `.planning/ROADMAP.md` - Phase 2 goal, requirements, success criteria, and Phase 8 deployment boundary.
- `.planning/REQUIREMENTS.md` - DATA-01..DATA-05 and PAY-01..PAY-03 traceability.
- `.planning/STATE.md` - current phase and continuity notes.
- `.planning/phases/01-backend-foundation-and-static-safety/01-CONTEXT.md` - locked backend stack/scope decisions.

### Vercel And Neon Official Docs
- `https://vercel.com/docs/frameworks/backend/fastapi` - FastAPI backend support pattern on Vercel.
- `https://vercel.com/docs/functions/runtimes/python` - Python runtime availability and constraints.
- `https://vercel.com/docs/functions/configuring-functions/duration` - function max duration settings and Hobby limits.
- `https://vercel.com/docs/functions/limitations` - function bundle, body size, filesystem, and runtime limits.
- `https://vercel.com/docs/postgres` - Vercel managed Postgres integration guidance.
- `https://vercel.com/marketplace/neon` - Neon as a Vercel Marketplace integration.
- `https://vercel.com/kb/guide/connection-pooling-with-functions` - serverless DB connection pooling guidance.
- `https://neon.com/pricing` - Neon free-first pricing context.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/db/base.py` - SQLAlchemy declarative base for future models.
- `backend/app/db/session.py` - async engine/sessionmaker; should be adjusted for serverless-friendly runtime settings when needed.
- `backend/alembic/env.py` - Alembic scaffold already bound to `Base.metadata`.
- `backend/docker-compose.yml` - local Postgres remains the local development database.
- `backend/.env.example` - Phase 2 should extend backend env documentation for database URLs, CORS, pricing, and future secrets.

### Established Patterns
- Backend is API-only and isolated inside `backend/`.
- Health endpoints stay unprefixed; business APIs should use `/api/v1/...`.
- Local checks are `python -m pytest`, `python -m ruff check .`, and `python -m ruff format --check .` from `backend/`.
- Docker image uses lean `requirements-runtime.txt`; dev/test tooling stays in `requirements.txt`.

### Integration Points
- Phase 2 schema will feed Phase 3 auth/profile bootstrap, Phase 4 wallet operations, Phase 5 comic persistence, Phase 6 generation jobs/pages, and Phase 8 production deployment.
- Future frontend integration should call backend at `api.comicly.ai` in production, but Phase 2 must not modify frontend files.

</code_context>

<specifics>
## Specific Ideas

- User prefers free-first MVP deployment and Vercel Hobby/free tier if practical.
- User accepts Vercel backend functions for MVP, with fallback to Render/Railway/Fly only if Vercel limitations become critical.
- User wants Codex to choose the Vercel path it can configure most independently.
- Production DB should use Neon/Vercel Marketplace rather than Docker Postgres.
- Generation jobs should exist in schema early, but MVP should stay simple and synchronous where possible.

</specifics>

<deferred>
## Deferred Ideas

- Real production deployment execution remains Phase 8 unless a Phase 2.1 deployment spike is later inserted.
- Real payment checkout and provider webhooks remain v2/out of current MVP scope.
- Queue/worker-based generation pipeline remains a future upgrade path after synchronous MVP.

</deferred>

---

*Phase: 02-data-and-payment-foundation*
*Context gathered: 2026-04-26*
