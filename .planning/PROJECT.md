# Comicly.ai

## What This Is

Comicly.ai is an AI comic creation web app. The current product is a static landing page plus a browser-based creator workspace that helps a user describe a story, manage scenes and pages, and generate comic page imagery through server-side OpenRouter calls.

The next project goal is to turn the demo-style creator into a production service: users can sign in, own their profile and coin balance, spend coins on generation, and return to a durable history of their comics.

## Core Value

Users can reliably create AI-generated comic pages under their own account, with durable comic history and trustworthy server-side coin accounting.

## Requirements

### Validated

- [x] Landing page exists with Comicly.ai branding, previews, workflow copy, pricing section, and navigation through `index.html`, `styles.css`, and `scripts/main.js`.
- [x] Creator workspace exists in `create.html`, `creator.css`, and `scripts/creator.js` with story input, style/tone/model controls, scene editing, page thumbnails, undo/redo, download/share actions, and user feedback toasts.
- [x] Local Node server exists in `server.js` and serves static files plus JSON API routes.
- [x] AI text generation exists through `POST /api/ai-text` for story enhancement, dialogue, captions, and scene suggestions.
- [x] AI comic page generation exists through `POST /api/generate-comic-page` using server-side OpenRouter credentials.
- [x] Local health/config feedback exists through `GET /api/health` and the creator configuration banner.

### Active

- [ ] Implement production-ready backend architecture without breaking the existing AI generation routes.
- [ ] Add OAuth login through Google and Yandex with secure server-side sessions.
- [ ] Store users, provider identities, profiles, wallets, coin transactions, comics, and comic pages in a database.
- [ ] Move coin balance and all debit/credit decisions to backend APIs, including transaction logs and insufficient-balance errors.
- [ ] Persist generated comics and pages so users can list, reopen, and continue their own work.
- [ ] Replace demo profile and hardcoded frontend credits with authenticated backend data.
- [ ] Prepare payment product and payment tables for future coin purchases, including seeded packages for 100, 500, and 1000 coins.
- [ ] Add deployment configuration, environment documentation, and local/production run instructions.
- [ ] Add safety gates: validation, auth protection, rate limiting, request idempotency, secure cookies, and tests around critical API behavior.

### Out of Scope

- Full payment-provider integration - database tables and package APIs are needed now, real acquiring/webhooks can come later.
- Admin panel - not required for the first production backend milestone.
- Email campaigns or notification emails - no current requirement depends on them.
- Role system - single normal-user access is enough for the current backend scope.
- Social features, public profiles, public comic feed, and publishing - comic history is private per user for now.
- Rebuilding the frontend in a framework - keep the current static frontend unless a later phase proves a framework migration is necessary.

## Context

The existing runtime is intentionally small: `server.js` uses Node core modules, reads local `.env`, serves files from the repository root, and proxies OpenRouter calls. The frontend is plain HTML/CSS/JavaScript with no build step. `scripts/creator.js` currently owns creator state, pages, scenes, credits, history, and demo profile behavior in browser memory.

The codebase map in `.planning/codebase/` identifies the main risks for production: repository-root static serving can expose private files, AI endpoints are unauthenticated, credits are only UI state, generated pages are not persisted, there is no database, there are no automated tests, and deployment is not configured.

The backend task spec in `backend/BACKEND_TZ.md` defines the intended production milestone: OAuth through Google/Yandex, DB-backed users and profiles, server-side coin wallet and transaction ledger, comic history, payment-ready tables, deployment, and acceptance criteria.

## Constraints

- **Tech stack**: Current runtime is plain Node.js `>=22`, static HTML/CSS/JS, and native `fetch`; preserve the existing app shape unless a backend phase deliberately introduces dependencies.
- **AI provider**: OpenRouter remains the existing AI integration boundary through server-side credentials.
- **Security**: Secrets must stay server-side; client code must not receive provider keys or trusted balance data.
- **Coins**: The database must be the source of truth for balances, and every balance change must be auditable through transactions.
- **Generation cost**: Full comic page generation costs 20 coins; scene regeneration costs 4 coins unless later product decisions change pricing.
- **Auth**: Sessions must use secure server-side validation and production-safe cookies.
- **Persistence**: Browser state can be a draft cache, but user-owned comics, pages, generated outputs, and balances must be persisted server-side.
- **Deployment**: The final service must have documented local setup and production deployment with required environment variables.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat the current app as brownfield, not greenfield | The creator UI and OpenRouter proxy already exist and should be preserved while production backend capabilities are added | Pending |
| Make backend wallet state authoritative | Frontend credits are bypassable and cannot support paid or private generation | Pending |
| Use Google and Yandex OAuth for v1 auth | The backend spec explicitly requires both providers and no separate password flow | Pending |
| Prepare payments without real provider integration | The data model must support future purchases, but actual acquiring/webhook work is out of current scope | Pending |
| Add tests before expanding risky backend behavior | Auth, static serving, coin debits, idempotency, and OpenRouter error handling have high regression risk | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. "What This Is" still accurate? Update if drifted.

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections.
2. Core Value check: still the right priority?
3. Audit Out of Scope: reasons still valid?
4. Update Context with current state.

---
*Last updated: 2026-04-25 after initialization*
