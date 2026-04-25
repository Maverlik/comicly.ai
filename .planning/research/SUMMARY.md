# Project Research Summary

**Project:** Comicly.ai
**Domain:** AI comic creation web app production backend
**Researched:** 2026-04-25
**Confidence:** HIGH for product/backend direction; MEDIUM for final hosting and async generation details

## Executive Summary

Comicly.ai is a brownfield AI comic creator: the static landing page and browser creator already exist, and the next milestone is to make the creator production-grade through authentication, durable user-owned comic history, server-side coin accounting, and safe OpenRouter-backed generation. The strongest research conclusion is to preserve the current static frontend and AI route contracts while replacing the prototype server internals with modular backend boundaries.

The recommended approach is a small Node 22 backend, preferably Express 5, with PostgreSQL, Drizzle, Arctic OAuth for Google/Yandex, Postgres-backed sessions, S3-compatible object storage, Zod validation, and Vitest/Supertest tests. The browser can keep fast draft editing state, but identity, profile, balance, debit decisions, comic ownership, generation jobs, and durable images must be owned by the backend and database.

The main risks are security and consistency failures during migration: repository-root static serving can expose private files, client-owned credits are bypassable, generation can double-charge without idempotency, and saved comics can become inconsistent if page persistence, image storage, and coin debits are not treated as one workflow. Mitigate these by building safety/module boundaries first, then schema/auth, then wallet/idempotency, then persistence/generation, with tests attached to every trust boundary.

## Stack Recommendation

The stack research recommends a conservative backend upgrade rather than a framework rewrite. Use Node.js 22+, Express 5, PostgreSQL, Drizzle ORM, Arctic OAuth, `express-session` plus `connect-pg-simple`, Zod, Helmet/rate limiting, S3-compatible storage such as Cloudflare R2, and Vitest/Supertest. Keep the current HTML/CSS/JS creator assets and preserve `POST /api/ai-text`, `POST /api/generate-comic-page`, and `GET /api/health` while moving implementation behind production services.

**Core technologies:**
- Node.js 22+: current runtime baseline with native `fetch`, Web Crypto, and modern JavaScript support.
- Express 5: low-friction route/middleware structure for the existing same-origin static app and JSON APIs.
- PostgreSQL: required for coin ledger transactions, constraints, idempotency, and ownership queries.
- Drizzle ORM + `pg`: SQL-shaped schema/migrations with escape hatches for wallet transaction logic.
- Arctic: small OAuth client for Google and Yandex without forcing a larger auth framework.
- Postgres-backed server sessions: opaque `HttpOnly` cookies with revocation and no browser-trusted claims.
- S3-compatible object storage: generated images and avatars should live outside Postgres and outside the repo.
- Vitest + Supertest: route and service coverage for static safety, auth, wallet, generation, and ownership.

**Critical version and deployment notes:**
- Pin Node 22+.
- Do not use `express-session` MemoryStore in production.
- Do not use SQLite or MongoDB for the production coin ledger.
- Vercel + Neon + R2 is a reasonable first deployment shape, but generation latency and hosting limits need production validation.

Sources: `.planning/PROJECT.md`, `.planning/research/STACK.md`

## Table-Stakes V1 Scope

The v1 backend milestone should convert visible demo capabilities into server-backed product capabilities. The core promise is: users sign in, see real profile and wallet data, spend server-accounted coins on AI generation, and return later to private saved comics and pages.

**Must have:**
- Google and Yandex OAuth login, return login, and logout with secure server-side sessions.
- Authenticated creator bootstrap through `/api/me` or equivalent, replacing demo profile and hardcoded credits.
- Server-side wallet balance plus append-only transaction ledger.
- Idempotent full-page generation at 20 coins and scene regeneration at 4 coins.
- Private comic/project persistence for title, story, characters, style, tone, scenes, pages, generated image metadata, status, and ownership.
- Durable generated page storage controlled by Comicly.ai, not provider-hosted URLs or browser memory.
- AI text assistance preserved through backend routes with auth, validation, and rate limits.
- Basic profile editing and avatar storage.
- Payment-ready package and payment tables, with seeded 100, 500, and 1000 coin packages, but no real checkout/webhook.
- Production safety gates: static allowlist/public directory, auth guards, request validation, rate limits, secure cookies, and critical tests.
- Deployment readiness: env docs, migration commands, host config, and production smoke checks.

**Preserve from current creator:**
- Project title, story, character editing, style/tone/model selection, scene editing, page thumbnails, AI assists, generation, download, and private share utility where compatible.

**Defer to v2+:**
- Real payment provider integration and webhook coin fulfillment.
- Admin panel and role system.
- Public profiles, public comic feed, social publishing, likes, comments, and collaboration.
- Email campaigns or notification emails.
- Password login.
- Frontend framework migration.
- Advanced model marketplace or dynamic per-model pricing UI.

Sources: `.planning/PROJECT.md`, `.planning/research/FEATURES.md`

## Architecture And Build Order

Architecture research recommends turning the single `server.js` into a modular backend-for-frontend that still serves the static UI. The key boundaries are HTTP app shell, router/middleware, auth/session service, persistence repositories, wallet/ledger service, generation/job service, comics/pages service, object storage adapter, payment-prep service, and safe static serving.

**Major components:**
1. HTTP app shell: startup, config validation, request IDs, error handling, and security headers.
2. Static server: explicit public directory or allowlist; no repository-root serving in production.
3. Auth/session service: Google/Yandex OAuth, provider identity linking, sessions, logout, and `/api/me`.
4. Persistence layer: migrations, repositories, ownership-safe queries, constraints, and seed data.
5. Wallet service: authoritative balance reads, debits, credits, refunds, ledger rows, and idempotency.
6. Generation service: OpenRouter client, prompt templates, model registry, validation, timeouts, jobs, and output parsing.
7. Comics/pages service: private comic drafts, scene/page order, generated page metadata, and owner checks.
8. Storage service: generated image and avatar objects with validated keys/URLs.
9. Payment-prep service: coin package catalog and future-compatible payment tables.

**Recommended build order:**
1. Backend foundation and static safety.
2. Database schema, migrations, repositories, and seed packages.
3. OAuth, sessions, current-user/profile bootstrap.
4. Wallet ledger, idempotency, and insufficient-balance behavior.
5. Comic persistence APIs and owner-scoped queries.
6. Production generation pipeline with jobs, storage copy, page persistence, and wallet debit.
7. Frontend backend integration to remove demo state and hydrate from APIs.
8. Deployment and operational hardening.

Sources: `.planning/research/ARCHITECTURE.md`, `.planning/research/STACK.md`

## Pitfalls And Guardrails

1. **Repository-root static serving can leak secrets and planning files.** Build static allowlist or `public/` first; deny dotfiles, `.planning/`, `backend/`, package metadata, traversal, unknown extensions, and validate `HEAD`.
2. **Adding auth into the current monolith will make every later change risky.** Extract app, config, routes, static, validation, OpenRouter, and error modules before adding deep auth/wallet logic.
3. **Client-owned credits or identity will break billing.** Never accept browser-sent balance, cost, user id, provider id, or owner id; derive them from session and database.
4. **Non-atomic generation, debit, and persistence can lose coins or create free pages.** Use a clear generation state machine, ledger rows, idempotency keys, and DB transactions around page persistence plus wallet updates.
5. **OpenRouter output is not durable history.** Copy successful images to controlled object storage before marking generated pages durable.
6. **OAuth and cookies can work locally but fail in production.** Validate redirect URIs, `APP_URL`, secure cookie flags, CSRF strategy, proxy HTTPS behavior, and logout invalidation.
7. **Cross-user comic access is easy to miss.** Every comic/page/job query must scope by authenticated `user_id`, with two-user tests.
8. **No tests means billing and auth regressions will ship.** Start tests in the foundation phase and expand them around static safety, auth, wallet, idempotency, OpenRouter failures, persistence, and deployment smoke checks.

Sources: `.planning/research/PITFALLS.md`

## Roadmap Implications

### Phase 1: Backend Foundation And Static Safety
**Rationale:** Production cannot safely add auth, cookies, or secrets while static serving exposes repository-root files and `server.js` remains an untestable monolith.  
**Delivers:** Modular app shell, safe static serving, config validation, normalized errors, request IDs, security headers, body validation scaffolding, and compatibility for existing AI routes.  
**Addresses:** Production safety gates and route preservation.  
**Avoids:** Repository file exposure, monolith coupling, health/config leakage, missing tests.

### Phase 2: Database Foundation
**Rationale:** Auth, wallet, comics, generation jobs, and payments all depend on durable schema and migrations.  
**Delivers:** PostgreSQL connection, Drizzle schema/migrations, repositories, constraints, seed coin packages, generation cost config, and test DB setup.  
**Addresses:** Users, provider identities, profiles, sessions, wallets, transactions, comics, pages, jobs, packages, and payment placeholders.  
**Avoids:** Schema rewrites, cross-user access gaps, payment table dead ends.

### Phase 3: OAuth Sessions And Current User
**Rationale:** Wallet and comic ownership must be tied to authenticated users before private APIs and paid generation are exposed.  
**Delivers:** Google/Yandex OAuth, server-side sessions, logout, `/api/me`, profile basics, first-login profile/wallet creation, starter coin grant through ledger.  
**Addresses:** OAuth account access and authenticated creator bootstrap.  
**Avoids:** provider email as primary key, insecure cookies, fake logout/profile state.

### Phase 4: Wallet Ledger And Idempotency
**Rationale:** Coin correctness must be proven before generation starts charging real backend balances.  
**Delivers:** Authoritative balance reads, debit/credit/refund operations, append-only ledger, insufficient-balance errors, idempotency table, reconciliation tests, stable error codes.  
**Addresses:** Server-side wallet, transaction ledger, full-page and scene-generation costs.  
**Avoids:** client credit trust, double charges, negative balances, mismatched ledger and wallet state.

### Phase 5: Comic Persistence
**Rationale:** Durable private history is central to the product and depends on auth plus schema.  
**Delivers:** Comic list/detail/create/update APIs, scene/page persistence, owner-scoped reads/writes, generated page metadata model, reload/reopen backend contract.  
**Addresses:** private comic/project persistence and generated page persistence.  
**Avoids:** lost work on refresh, cross-user comic reads, browser-only history.

### Phase 6: Production Generation Pipeline
**Rationale:** This is where provider cost, durable assets, page state, and wallet debits meet; it should be built after wallet and persistence boundaries exist.  
**Delivers:** Authenticated generation route, idempotency key enforcement, generation jobs, OpenRouter timeouts/fixtures, object storage copy, page persistence, wallet debit transaction, updated balance response.  
**Addresses:** paid full-page generation, scene regeneration, AI route preservation, durable images.  
**Avoids:** duplicate provider calls, hung requests, broken image history, coin loss on provider/storage failures.

### Phase 7: Frontend Backend Integration
**Rationale:** The static creator should stay intact while data sources move from in-memory demo state to authenticated APIs.  
**Delivers:** API client wrapper, `/api/me` hydration, real balance/profile display, comic list/reopen flow, backend generation response handling, removal of demo-only credit/profile/logout paths.  
**Addresses:** visible user-facing completion of the v1 backend.  
**Avoids:** demo state fighting backend truth, undo restoring trusted server state, unsafe URL rendering.

### Phase 8: Deployment And Operations
**Rationale:** Production acceptance requires validated host behavior, environment configuration, OAuth redirects, database/storage connectivity, secure cookies, and smoke tests.  
**Delivers:** deployment config, `.env.example`, runbook, migration docs, production health/readiness behavior, logging, rate limits, smoke tests, and host-specific validation.  
**Addresses:** deployment readiness and production safety gates.  
**Avoids:** missing secrets, runtime mismatch, serverless timeout surprises, local-only OAuth/cookie behavior.

### Phase Ordering Rationale

- Static safety and modular boundaries come first because every later feature increases the damage of an exposed repo root or tangled route code.
- Database work precedes OAuth completion so first login can create user, identity, profile, session, wallet, and starter ledger rows correctly.
- Wallet/idempotency precedes paid generation because OpenRouter calls create real cost and billing must not rely on browser state.
- Comic persistence precedes final generation integration so generated results can attach to owned, durable comic/page records.
- Frontend integration follows backend capability to avoid replacing demo state with incomplete or untrusted API behavior.
- Deployment hardening closes the milestone after all trust boundaries exist, while early phases still keep deployment constraints visible.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** OAuth provider details, redirect URI behavior, session cookie policy, and Yandex-specific identity fields should be verified against current docs.
- **Phase 6:** OpenRouter image response shapes, timeouts, retry behavior, object storage ingestion, and sync-vs-async generation limits need implementation-level validation.
- **Phase 8:** Final hosting provider, database provider, function duration, connection pooling, OAuth callbacks, and object storage config need environment-specific research.

Phases with standard patterns where extra research can usually be skipped:
- **Phase 1:** Express app extraction, static allowlists, validation scaffolding, and route tests are well-documented.
- **Phase 2:** PostgreSQL/Drizzle migrations and seed data are standard once the provider is selected.
- **Phase 4:** Ledger/idempotency needs careful design, but the core transaction and unique-key patterns are standard.
- **Phase 5:** Owner-scoped CRUD APIs and private history persistence are standard backend patterns.
- **Phase 7:** Static frontend API hydration is straightforward after backend contracts are stable.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Strong alignment with existing Node/static app and official docs cited in `.planning/research/STACK.md`; deployment provider remains MEDIUM. |
| Features | HIGH | V1 scope is grounded in `.planning/PROJECT.md`, current creator UI, backend spec, and codebase concerns. |
| Architecture | HIGH | Component boundaries and build order directly address current code risks; async generation details remain MEDIUM. |
| Pitfalls | HIGH | Pitfalls are project-specific and backed by current code/planning docs; operational risks depend on final host/storage choices. |

**Overall confidence:** HIGH for roadmap sequencing and backend scope; MEDIUM for final production infrastructure choices.

### Gaps To Address

- **Final deployment provider:** Validate Vercel/Neon/R2 versus another long-running host before locking deployment tasks.
- **Synchronous vs queued generation:** Start with synchronous persisted jobs if acceptable, but confirm OpenRouter latency and host timeouts before launch.
- **Starter coin amount:** Keep configurable and record grants through ledger; product decision still needs confirmation.
- **Object storage provider and URL strategy:** Use an adapter, but choose production storage before generation persistence implementation.
- **Payment schema details:** Include future webhook/idempotency fields now, but defer real provider-specific flow.

## Sources

### Primary
- `.planning/PROJECT.md` - project goal, active requirements, constraints, out-of-scope items, and key decisions.
- `.planning/research/STACK.md` - recommended backend stack, deployment shape, database/wallet model, and phase implications.
- `.planning/research/FEATURES.md` - table-stakes v1 capabilities, deferred work, current creator behavior to preserve, and acceptance implications.
- `.planning/research/ARCHITECTURE.md` - target components, data flow, build order, migration constraints, and component boundaries.
- `.planning/research/PITFALLS.md` - critical/moderate/minor pitfalls, guardrails, phase warning matrix, and required tests.

### Referenced By Research
- `.planning/codebase/ARCHITECTURE.md` - current codebase architecture and missing production boundaries.
- `.planning/codebase/CONCERNS.md` - security, persistence, AI endpoint, and testing risks.
- `.planning/codebase/TESTING.md` - absence of test framework and recommended test targets.
- `backend/BACKEND_TZ.md` - backend target spec for OAuth, profiles, wallets, comics, payments-ready data, and deployment.
- `server.js` - current prototype server, static serving, health route, and OpenRouter proxy.
- `create.html` - current creator UI affordances for account, credits, story, scenes, models, generation, and profile actions.
- `scripts/creator.js` - current browser-owned creator state, demo credits/profile, generation calls, and UI behavior.

---
*Research completed: 2026-04-25*
*Ready for roadmap: yes*
