# Phase 1: Backend Foundation And Static Safety - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 prepares a standalone API-only backend foundation inside `backend/`. It does not implement the full business backend from `backend/BACKEND_TZ.md`; it creates the structure needed to implement that spec safely in later phases.

Phase 1 scope is limited to backend foundation: Python project structure, dependencies, Docker app plus Postgres, config/env handling, base FastAPI app, `/health`, `/ready`, static safety posture, test infrastructure, lint/format tooling, and starter documentation.

The existing frontend and other root project files must not be changed without separate user confirmation. If planning finds a needed change outside `backend/`, the plan must isolate it as a checkpoint requiring approval before implementation.

</domain>

<decisions>
## Implementation Decisions

### Backend Ownership And Scope
- **D-01:** Backend must be implemented only inside `backend/` for Phase 1.
- **D-02:** Backend is a standalone API-only service, not a server for the existing frontend.
- **D-03:** Frontend files such as `index.html`, `create.html`, `scripts/main.js`, `scripts/creator.js`, `styles.css`, and `creator.css` are out of scope for Phase 1.
- **D-04:** Any required changes outside `backend/` must be explained first and explicitly confirmed by the user before implementation.
- **D-05:** `backend/BACKEND_TZ.md` is the primary source of truth for backend requirements and must be read before planning or implementation.

### Stack
- **D-06:** Use Python 3.12 as the backend runtime.
- **D-07:** Use FastAPI for the API framework.
- **D-08:** Use PostgreSQL as the database.
- **D-09:** Use SQLAlchemy 2 async ORM patterns with Alembic migrations.
- **D-10:** Use `asyncpg` as the PostgreSQL async driver.
- **D-11:** Use ordinary `pip` plus `requirements.txt` for dependencies. Do not use `uv` or Poetry in Phase 1.
- **D-12:** Use Pydantic Settings or equivalent Pydantic-based config loading for environment configuration.
- **D-13:** Use `httpx` later for outbound OpenRouter calls when AI routes are implemented or migrated.
- **D-14:** Use Authlib later for Google/Yandex OAuth unless Phase 3 research finds a stronger Python-native option.

### Docker And Local Runtime
- **D-15:** Phase 1 should include Docker support for both backend app and PostgreSQL.
- **D-16:** The backend should be able to run as its own container next to Postgres, anticipating future separation from the frontend and possible extraction to a separate repository/service.
- **D-17:** The local database should be available through Docker Compose in `backend/`.

### API Shape
- **D-18:** Health endpoints stay unprefixed: `GET /health` and `GET /ready`.
- **D-19:** `GET /health` should be a lightweight process/app health response.
- **D-20:** `GET /ready` should check readiness dependencies, including database connectivity once the DB wiring exists.
- **D-21:** Business API routes in later phases should live under `/api/v1/...`.
- **D-22:** Phase 1 should not add business routes except minimal health/readiness endpoints and any framework-generated docs that FastAPI exposes by default.

### Static Safety
- **D-23:** Because this backend is API-only, it should not serve repository-root static files or frontend assets in Phase 1.
- **D-24:** Static safety for Phase 1 means the backend foundation must make accidental static exposure difficult: no root static mount, no `.env`/planning/backend-doc serving, and no implicit file server behavior.
- **D-25:** If a future phase needs the backend to serve frontend assets, that must be separately discussed and planned.

### Tests And Quality Gates
- **D-26:** Use Pytest for tests.
- **D-27:** Use HTTPX/FastAPI test client patterns for API tests.
- **D-28:** Phase 1 tests should cover `/health`, `/ready`, config loading behavior, app startup wiring, and the absence of unintended static serving.
- **D-29:** Use Ruff for linting and formatting.
- **D-30:** Phase 1 should add clear scripts or documented commands for lint, format/check, tests, migrations, and local Docker startup.

### the agent's Discretion
- Exact Python package/module naming inside `backend/`.
- Exact `requirements.txt` split strategy, as long as setup stays understandable and standard.
- Exact health response JSON shape, as long as `/health` and `/ready` are distinct and stable.
- Exact Docker Compose service names and local ports, as long as they are documented and do not conflict unnecessarily with the existing frontend.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backend Requirements
- `backend/BACKEND_TZ.md` - primary source of truth for the backend product, auth, wallet, comic history, payment-prep, deployment, security, and acceptance requirements.

### GSD Project Context
- `.planning/PROJECT.md` - project definition, core value, active requirements, constraints, and decisions.
- `.planning/REQUIREMENTS.md` - v1 requirement IDs and traceability.
- `.planning/ROADMAP.md` - Phase 1 goal, requirements, and success criteria.
- `.planning/STATE.md` - current phase and continuity notes.

### Codebase Map
- `.planning/codebase/STACK.md` - current frontend/root Node prototype stack.
- `.planning/codebase/ARCHITECTURE.md` - current static frontend plus prototype server architecture.
- `.planning/codebase/CONCERNS.md` - static serving, unauthenticated AI, client-only state, and missing backend concerns.
- `.planning/codebase/STRUCTURE.md` - current directory purposes and where `backend/` currently fits.
- `.planning/codebase/TESTING.md` - current absence of tests and recommended coverage areas.

### Project Research
- `.planning/research/SUMMARY.md` - prior project-level research; use cautiously because this context supersedes its Node/Express recommendation.
- `.planning/research/STACK.md` - prior stack comparison; superseded for Phase 1 by the user's Python/FastAPI decision in this context.
- `.planning/research/ARCHITECTURE.md` - prior component-boundary research; adapt concepts to standalone Python API backend.
- `.planning/research/PITFALLS.md` - backend trust-boundary and coin/idempotency risks that remain relevant.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/BACKEND_TZ.md`: the backend requirements document is the anchor for all backend planning.
- `.env.example`: may inform required env naming, but Phase 1 should create/update backend-specific env docs in `backend/` if needed.

### Established Patterns
- Current frontend is static and should remain independent from the backend during Phase 1.
- Current root `server.js` is a prototype/static server/OpenRouter proxy and should not be treated as the target backend architecture.
- Existing AI endpoints are useful product context, but Phase 1 should not migrate business behavior yet.

### Integration Points
- Future frontend integration will likely call the standalone backend API over HTTP.
- Future business routes should be placed under `/api/v1/...`.
- Future phases will implement auth, DB schema, wallet ledger, comic persistence, and OpenRouter integration based on `backend/BACKEND_TZ.md`.

</code_context>

<specifics>
## Specific Ideas

- The user prefers Python/FastAPI because they know that stack better and want the backend/frontend to be independent entities.
- The user intentionally chose `pip + requirements.txt` over `uv` or Poetry for maximum simplicity and standard MVP setup.
- The backend may later move out of this repo or run as a neighboring container in Docker Compose.
- Phase 1 should prepare foundation only; business features from `backend/BACKEND_TZ.md` belong to later phases.

</specifics>

<deferred>
## Deferred Ideas

- Google/Yandex OAuth implementation - later auth phase.
- Wallet ledger, coin debits, idempotency, and race-condition protection - later wallet phase.
- Comic persistence and page history - later persistence phase.
- OpenRouter route migration/generation pipeline - later generation phase.
- Frontend integration with backend API - later frontend integration phase and requires separate permission to change frontend files.
- Production deployment - later operations phase.

</deferred>

---

*Phase: 01-backend-foundation-and-static-safety*
*Context gathered: 2026-04-26*
