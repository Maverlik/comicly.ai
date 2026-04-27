---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: ready_for_discussion
stopped_at: Phase 4 context gathered; ready to plan
last_updated: "2026-04-27T18:10:55+03:00"
last_activity: 2026-04-27 -- Phase 4 context gathered
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 10
  completed_plans: 10
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-25)

**Core value:** Users can reliably create AI-generated comic pages under their own account, with durable comic history and trustworthy server-side coin accounting.
**Current focus:** Phase 4 - Wallet Ledger And Coin Safety

## Current Position

Phase: 4 (Wallet Ledger And Coin Safety) - READY TO PLAN
Plan: 0 of TBD
Status: Phase 4 context gathered; ready to plan
Last activity: 2026-04-27 -- Phase 4 context gathered

Progress: [----------] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 3
- Average duration: 7 min
- Total execution time: 0.37 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 1 | 3 | 22 min | 7 min |

**Recent Trend:**

- Last 5 plans: 01-02, 01-03, 02-01, 02-02, 02-03
- Trend: Backend foundation plus data/payment foundation completed with schema, seed, catalog, and quality gates

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Standard granularity produced 8 production-backend phases derived from the v1 requirements and research build order.
- [Roadmap]: Static safety and module boundaries come before auth, wallet, and generation because repository-root serving and the monolithic server are production blockers.
- [Roadmap]: Payment work in v1 is schema/catalog preparation only; real checkout and webhook fulfillment remain v2.
- [Phase 1 Plan 01]: New FastAPI backend remains API-only with no static file mount or repository-root file access.
- [Phase 1 Plan 01]: Phase 1 settings require only app name/env/debug and database URL; OAuth, OpenRouter, storage, and session secrets remain deferred.
- [Phase 1 Plan 02]: `/health` is dependency-free and returns only process status.
- [Phase 1 Plan 02]: `/ready` is database-backed and maps DB failures to `DATABASE_UNAVAILABLE` without leaking connection details.
- [Phase 1 Plan 02]: Alembic is bound to `Base.metadata`, with business schema creation deferred to later data phases.
- [Phase 1 Plan 03]: Static safety is verified as an API-only negative guarantee: no StaticFiles mount and representative private/root/frontend paths are not served by FastAPI.
- [Phase 1 Plan 03]: Existing root Node AI routes remain owned by the root runtime until a later approved migration plan changes frontend/root behavior.
- [Phase 1 Plan 03]: Backend quality gates are `python -m pytest`, `python -m ruff check .`, and `python -m ruff format --check .` from `backend/`.
- [Phase 1 Verification]: Pytest passed 15/15, Ruff lint/format passed, `docker compose config` passed, `docker compose up -d --build` passed, and Docker `/health` plus `/ready` smoke tests returned healthy responses.
- [Phase 2 Discussion]: MVP deployment is Vercel-first with separate frontend/backend projects, frontend on `comicly.ai`/`www.comicly.ai`, backend API on `api.comicly.ai`, Neon pooled `DATABASE_URL` for runtime, and direct migration DB URL if needed for Alembic.
- [Phase 2 Discussion]: Generation jobs should be represented in schema for future queue/status polling, while MVP generation may remain synchronous within Vercel Hobby limits.
- [Phase 2 Verification]: Alembic migration, metadata/constraint tests, seed script, `/api/v1/coin-packages`, docs, pytest, ruff, and code review all passed.
- [Phase 3 Discussion]: OAuth is backend-owned redirect flow for Google/Yandex, successful login redirects to `comicly.ai/create.html`, sessions are opaque DB-backed cookies for 30 days, providers link by verified email, Phase 3 is backend API-only, and avatar upload is deferred until storage is selected.
- [Phase 3 Verification]: Google/Yandex OAuth route surfaces, provider normalization, first-login bootstrap, verified-email linking, `/api/v1/me`, display-name update, and current-session logout are implemented and covered by mocked provider/session tests.
- [Phase 4 Discussion]: Wallet ledger scope is backend-only foundation: `GET /api/v1/wallet` balance plus recent transactions, debit-before-generation primitives with refund support, required `Idempotency-Key` for billable operations, and no real generation/frontend integration until later phases.

### Pending Todos

None yet.

### Blockers/Concerns

- Object storage provider remains open and should be decided before Phase 6/8 implementation details are locked.
- Production deployment target is Vercel-first, but backend portability should be preserved for Render/Railway/Fly fallback if Vercel limitations become critical.
- Starter coin amount should remain configurable until product value is confirmed.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Payments | Real payment checkout, provider webhooks, and purchased coin fulfillment | v2 | 2026-04-25 |
| Product | Public profiles, public gallery/feed, social publishing, collaboration, and notifications | v2 | 2026-04-25 |
| Frontend | Full framework migration and dynamic model marketplace | v2 | 2026-04-25 |

## Session Continuity

Last session: 2026-04-27T18:10:55+03:00
Stopped at: Phase 4 context gathered; ready to plan
Resume file: .planning/phases/04-wallet-ledger-and-coin-safety/04-CONTEXT.md
