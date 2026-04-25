# AGENTS.md

## Project

Comicly.ai is a brownfield AI comic creation app. The current runtime is a static HTML/CSS/JavaScript frontend plus a small Node.js server that serves files and proxies OpenRouter AI calls.

Current project focus is the production backend milestone: preserve the existing creator and AI route contracts while adding safe static delivery, database-backed auth/profile/wallet/comic persistence, trustworthy coin accounting, durable generation results, and deployment readiness.

## Planning Context

Read these before planning or executing non-trivial work:

- `.planning/PROJECT.md` - living project definition, core value, constraints, and decisions.
- `.planning/ROADMAP.md` - phase order and success criteria.
- `.planning/STATE.md` - current phase and continuity notes.
- `.planning/REQUIREMENTS.md` - v1 requirement IDs and phase traceability.
- `.planning/codebase/` - current codebase map.
- `.planning/research/SUMMARY.md` - project research summary and roadmap implications.

Current focus:

- Phase 1: Backend Foundation And Static Safety.
- Goal: make the backend safe to extend for production without exposing private files or breaking current AI route contracts.

## Commands

- Start app: `npm start`
- There is currently no test script. Add automated tests as part of Phase 1 before relying on test gates.

## Codebase Shape

- `server.js` is the current Node entry point, static server, and OpenRouter API proxy.
- `index.html`, `styles.css`, and `scripts/main.js` implement the landing page.
- `create.html`, `creator.css`, and `scripts/creator.js` implement the creator workspace.
- `assets/` contains static images used by the app.
- `backend/BACKEND_TZ.md` contains the production backend specification.

## Guardrails

- Do not expose repository-root files through static serving. Deny `.env`, `.planning/`, `backend/`, dotfiles, package metadata, and traversal attempts.
- Do not trust browser-sent identity, owner ids, credit balances, generation costs, or payment state.
- Keep OpenRouter credentials server-side.
- Preserve compatibility for `GET /api/health`, `POST /api/ai-text`, and `POST /api/generate-comic-page` unless a migration plan updates the frontend and requirements.
- Coin state must be database-authoritative and auditable through transaction rows.
- Generation debits must be idempotent and safe under retries or double clicks.
- User comic data must be owner-scoped.
- Keep real payment-provider integration, admin UI, public profiles/feed, social features, role system, and frontend framework migration out of v1 unless the roadmap is explicitly updated.

## GSD Flow

- Next normal command: `$gsd-plan-phase 1`
- For frontend-heavy phases, run `$gsd-ui-phase <phase>` before planning when the roadmap marks a UI hint.
- Keep planning docs committed as atomic checkpoints.
- Update `.planning/STATE.md` when phase position changes.

---
*Generated: 2026-04-25 during project initialization*
