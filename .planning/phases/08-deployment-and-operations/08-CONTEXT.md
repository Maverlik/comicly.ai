# Phase 8: Deployment And Operations - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 makes the completed MVP backend and static frontend deployable and operable for production.

In scope: environment examples, local setup/run instructions, Vercel-first production deployment docs/config, Neon Postgres runtime/migration URL handling, Vercel Blob configuration, OAuth callback/domain/cookie configuration, production smoke checks, basic security headers, and basic rate limiting for sensitive API surfaces.

Out of scope: new business features, payment checkout/webhooks, admin UI, public gallery/social features, frontend framework migration, async queue/worker generation rewrite, and enterprise observability.

</domain>

<decisions>
## Implementation Decisions

### Deployment Execution
- **D-01:** Use a practical Vercel-first path for the MVP.
- **D-02:** Planning/execution should prepare required repo config and docs, then attempt real Vercel setup/deploy through available tools/CLI when credentials and project access allow.
- **D-03:** If Vercel access, project linkage, domains, marketplace secrets, or provider credentials block full automation, do not stall the phase. Record the exact manual checklist and any remaining verification gaps.
- **D-04:** Keep the backend portable; do not move business logic into Vercel-only platform features.

### Vercel Project Shape
- **D-05:** Use two Vercel projects from the same repository:
  - root/static frontend project for `comicly.ai` and `www.comicly.ai`;
  - `backend/` FastAPI API project for `api.comicly.ai`.
- **D-06:** Do not use Docker Compose for production on Vercel. Docker Compose remains local-only.
- **D-07:** Avoid depending on Vercel Services for the MVP because the safer path is a separate backend project rooted at `backend/`.

### Secrets And Environment
- **D-08:** Never commit real secrets or tokens.
- **D-09:** Update environment examples and deployment docs/checklists so required local and production variables are explicit.
- **D-10:** Production secrets/settings belong in Vercel environment variables and provider integrations, not in committed files.
- **D-11:** Runtime app database access uses the Neon pooled connection URL as `DATABASE_URL`, converted to the async SQLAlchemy driver form.
- **D-12:** Alembic migrations use a direct non-pooled Neon URL through `MIGRATION_DATABASE_URL` when available, with `DATABASE_DIRECT_URL` as accepted fallback.
- **D-13:** Vercel Blob uses `BLOB_READ_WRITE_TOKEN`; OpenRouter uses `OPENROUTER_API_KEY`; OAuth uses provider client IDs/secrets and registered production callback URLs.

### Production Smoke Scope
- **D-14:** Required smoke should cover production/public reachability and configuration shape first: frontend public page, creator auth entry, `/health`, `/ready`, CORS/cookie behavior, and OAuth login link routing.
- **D-15:** Live Google/Yandex OAuth callback and live generation with Blob/OpenRouter should be verified in Phase 8 when the production secrets/providers are configured.
- **D-16:** If live provider secrets or domain/provider configuration are unavailable during execution, leave an explicit manual verification checklist rather than faking success.
- **D-17:** Generation must keep returning durable `image_url` values, not large base64 payloads, to stay within serverless request/response limits.

### Security And Operations Minimum
- **D-18:** Add basic backend security headers in the production API path.
- **D-19:** Add simple portable in-process rate limiting for sensitive endpoints: OAuth/auth routes, profile writes, AI text, generation, and other write/billable paths.
- **D-20:** Do not make Vercel Firewall or platform-only rate limiting the primary MVP control. It may be documented as an optional later/harderening layer if free-tier support is available.
- **D-21:** Keep `/health` dependency-free and `/ready` dependency-aware without leaking secrets or provider config.

### the agent's Discretion
- Exact Vercel config file shape, CLI commands, and docs layout.
- Exact rate-limit thresholds, as long as they are conservative enough for MVP abuse control and do not break normal creator use.
- Exact production smoke implementation, as long as it distinguishes automated checks from manual provider-secret-dependent checks.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Scope
- `.planning/PROJECT.md` - project constraints, deployment target, backend truth principles, and v1/v2 boundary.
- `.planning/ROADMAP.md` - Phase 8 goal and success criteria.
- `.planning/REQUIREMENTS.md` - `OPS-01` through `OPS-05`.
- `.planning/STATE.md` - current phase position and continuity notes.
- `backend/BACKEND_TZ.md` - backend source-of-truth specification.

### Prior Phase Decisions
- `.planning/phases/02-data-and-payment-foundation/02-CONTEXT.md` - Vercel-first deployment, separate frontend/backend projects, Neon pooled runtime URL, direct migration URL.
- `.planning/phases/03-oauth-sessions-and-profile-bootstrap/03-CONTEXT.md` - OAuth redirect/session/cookie decisions, 30-day sessions, provider callback implications.
- `.planning/phases/06-production-ai-generation-pipeline/06-CONTEXT.md` - synchronous MVP generation, Vercel Blob, no base64 responses, generation job future queue readiness.
- `.planning/phases/07-creator-frontend-backend-integration/07-CONTEXT.md` - frontend backend API base URL, creator auth entry, production frontend/backend integration boundaries.
- `.planning/phases/07-creator-frontend-backend-integration/07-VERIFICATION.md` - latest verified app behavior and known live-secret-dependent manual gaps.

### Backend Files
- `backend/.env.example` - existing backend env example to update and make production-complete.
- `backend/README.md` - existing local/backend docs to update for deployment and operations.
- `backend/app/core/config.py` - settings/env source of truth, production cookie validation, DB URL precedence.
- `backend/app/main.py` - middleware registration point for security headers and rate limiting.
- `backend/alembic/env.py` - migration URL handling.
- `backend/requirements.txt` and `backend/requirements-runtime.txt` - dependency lists for local/dev and production runtime.
- `backend/docker-compose.yml` - local-only Postgres/backend stack.

### Frontend And Root Files
- `.env.example` - root frontend/legacy env documentation; may need safe documentation updates only.
- `package.json` - root static frontend scripts and Phase 7 test script.
- `server.js` - current local static server; production frontend deployment must not expose private repo files.
- `scripts/creator.js` - frontend API base URL logic for local vs production `api.comicly.ai`.

### Official Deployment References
- `https://vercel.com/docs/functions/runtimes/python` - Vercel Python runtime/FastAPI deployment reference; Python runtime is Beta.
- `https://vercel.com/docs/functions/configuring-functions/duration` - function duration configuration and Hobby/Fluid Compute limit context.
- `https://vercel.com/docs/functions/limitations` - serverless request/response/body and execution limitations.
- `https://vercel.com/docs/postgres` - Vercel Marketplace Postgres/Neon setup context.
- `https://vercel.com/docs/vercel-blob/usage-and-pricing` - Vercel Blob limits/pricing context for free-first storage.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- FastAPI already has settings, health/readiness routes, CORS, session middleware, API error envelopes, and v1 routers.
- Backend docs already cover local setup, Docker Compose, env vars, migrations, seed data, wallet ledger, generation pipeline, and private comic persistence.
- Backend tests already cover core API behavior; Phase 8 can add focused tests for security headers, rate limiting, config/docs contracts, and deploy config shape.
- Creator frontend already points local API calls to `http://localhost:8000` and production API calls to `https://api.comicly.ai`.

### Established Patterns
- Backend is API-only and must not serve repository-root/static frontend files.
- Local development uses Docker Compose/PostgreSQL under `backend/`.
- Production DB should use Neon pooled runtime URL plus direct migration URL.
- All business APIs live under `/api/v1/...`; `/health` and `/ready` remain unprefixed.
- Quality gates remain `python -m pytest`, `python -m ruff check .`, and `python -m ruff format --check .` from `backend/`, plus relevant root/static smoke checks when frontend/root files are touched.

### Integration Points
- Vercel backend project needs a FastAPI-compatible entrypoint/config rooted in `backend/`.
- Production env docs must align with `Settings` fields in `backend/app/core/config.py`.
- OAuth provider callback URLs must use `https://api.comicly.ai/api/v1/auth/{provider}/callback`.
- Cookie settings must support frontend on `comicly.ai`/`www.comicly.ai` and backend on `api.comicly.ai`.
- Production smoke must distinguish automated endpoint checks from live provider checks that require real OAuth/OpenRouter/Blob configuration.

</code_context>

<specifics>
## Specific Ideas

- Preferred production domains:
  - frontend: `https://comicly.ai` and `https://www.comicly.ai`;
  - backend API: `https://api.comicly.ai`.
- Free-first MVP is important. Use Vercel Hobby/free where practical, Neon/Vercel Marketplace for managed Postgres, and Vercel Blob for generated image persistence.
- Keep synchronous generation for MVP, but document that frequent duration failures should trigger a future async polling/queue/worker phase.
- Do not hide deployment blockers. If a provider/domain/secret step cannot be completed by Codex, capture the exact missing action.

</specifics>

<deferred>
## Deferred Ideas

- Async generation polling/queue/worker pipeline.
- Vercel Firewall or provider-level WAF/rate limiting as a hard dependency.
- Full observability stack with external tracing/error monitoring.
- CI/CD pipeline beyond minimal deploy/readiness guidance.
- Payment checkout/webhook deployment operations.

</deferred>

---

*Phase: 08-deployment-and-operations*
*Context gathered: 2026-04-29*
