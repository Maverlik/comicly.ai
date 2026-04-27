# Roadmap: Comicly.ai Production Backend

## Overview

This milestone turns the existing static Comicly.ai creator and prototype Node AI proxy into a production backend service. The path preserves the current creator and OpenRouter route contracts while adding safe static delivery, durable PostgreSQL-backed data, OAuth sessions, authoritative coin accounting, private comic history, production generation persistence, frontend hydration from trusted APIs, and deployment readiness.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Backend Foundation And Static Safety** - Modularize the server, lock down static/API safety, and preserve existing AI routes.
- [x] **Phase 2: Data And Payment Foundation** - Add migrations, constraints, runtime pricing config, seeded coin packages, and payment-ready schema.
- [x] **Phase 3: OAuth Sessions And Profile Bootstrap** - Let users sign in with Google/Yandex, manage profile basics, and receive secure server-side sessions.
- [ ] **Phase 4: Wallet Ledger And Coin Safety** - Make balances authoritative through backend ledger operations, idempotency, and concurrency-safe debits.
- [ ] **Phase 5: Private Comic Persistence** - Persist user-owned comic drafts, scenes, pages, and owner-scoped history.
- [ ] **Phase 6: Production AI Generation Pipeline** - Connect protected OpenRouter generation to jobs, durable storage, page persistence, and updated balance responses.
- [ ] **Phase 7: Creator Frontend Backend Integration** - Replace demo creator state with authenticated backend profile, balance, comic, and generation data.
- [ ] **Phase 8: Deployment And Operations** - Document and verify local and production operation, deployment configuration, and operational safety gates.

## Phase Details

### Phase 1: Backend Foundation And Static Safety
**Goal**: The backend is safe to extend for production without exposing private files or breaking current AI route contracts.
**Depends on**: Nothing (first phase)
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, OPS-06, TEST-01
**Success Criteria** (what must be TRUE):
  1. Developer can run `npm start` and still use `GET /api/health`, `POST /api/ai-text`, and `POST /api/generate-comic-page` through migration-compatible contracts.
  2. Public static requests only return intended app files and assets; `.env`, `.planning/`, `backend/`, package metadata, traversal attempts, dotfiles, and unknown private paths are denied.
  3. Invalid API bodies, query strings, and route parameters return consistent JSON errors with stable machine-readable codes before business logic runs.
  4. Public health/readiness responses are production-safe and do not expose secrets, configured provider keys, or sensitive model configuration.
  5. Developer can run automated tests covering static file safety, traversal and dotfile denial, API error format, and legacy AI route compatibility.
**Plans**: 3 plans
Plans:
- [x] 01-01-PLAN.md — Backend project scaffold, config, error envelope, and Docker foundation.
- [x] 01-02-PLAN.md — FastAPI health/readiness endpoints plus SQLAlchemy async DB and Alembic foundation.
- [x] 01-03-PLAN.md — Pytest/Ruff quality gates, static-safety coverage, documentation, and AI route migration boundary.

### Phase 2: Data And Payment Foundation
**Goal**: Durable schema, constraints, seed data, and configuration exist for users, sessions, wallets, comics, generation, and future payments.
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, PAY-01, PAY-02, PAY-03
**Success Criteria** (what must be TRUE):
  1. Developer can run migrations from a clean checkout and create all production backend tables required for identity, profiles, sessions, wallets, comics, generation jobs, coin packages, and payment placeholders.
  2. Database constraints reject duplicate provider identities, duplicate idempotency keys, invalid wallet balances, and cross-owner comic or page relationships.
  3. Developer can seed active 100, 500, and 1000 coin packages, and authenticated product code can fetch the active package catalog from the backend.
  4. Generation costs and starter coins are defined through runtime configuration rather than scattered hardcoded frontend and backend literals.
  5. Payment placeholder records can represent status, user, package, amount, currency, external provider fields, and future webhook idempotency without wallet schema redesign.
**Plans**: 3 plans
Plans:
- [x] 02-01-PLAN.md — Serverless-aware settings plus SQLAlchemy models for identity, wallet, comics, generation jobs, coin packages, and payments.
- [x] 02-02-PLAN.md — Initial Alembic schema migration with direct migration URL handling and production constraints.
- [x] 02-03-PLAN.md — Idempotent coin package seed, active package catalog API, pricing/env docs, and quality gates.

### Phase 3: OAuth Sessions And Profile Bootstrap
**Goal**: Users can securely access their accounts, and account/profile/wallet bootstrap data is created and returned by trusted backend APIs.
**Depends on**: Phase 2
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07, PROF-01, PROF-02, TEST-02
**Success Criteria** (what must be TRUE):
  1. User can sign in with Google OAuth and receive a secure server-side session cookie.
  2. User can sign in with Yandex OAuth, and returning logins attach to the existing provider identity by provider and provider user id.
  3. First OAuth login creates the user, provider identity, profile, wallet, and starter coin ledger entry, then `GET /api/v1/me` returns account, profile, and wallet summary.
  4. User can update display name and receive an OAuth-provided avatar URL when available; real avatar file upload is deferred until object storage is selected.
  5. User can log out, the server invalidates the session, anonymous private API requests are rejected, and session cookies are `HttpOnly`, production `Secure`, and use an appropriate `SameSite` policy.
**Plans**: 4 plans
Plans:
- [x] 03-01-PLAN.md — Auth config, product session helpers, OAuth state middleware, CORS/cookie safety.
- [x] 03-02-PLAN.md — Google/Yandex OAuth route surface, provider normalization, first-login bootstrap, verified-email linking.
- [x] 03-03-PLAN.md — Current-user dependency, `/api/v1/me`, display-name update, logout.
- [x] 03-04-PLAN.md — OAuth/session docs, env example updates, full backend quality gates and boundary check.

### Phase 4: Wallet Ledger And Coin Safety
**Goal**: Coin balances and every balance-changing decision are authoritative, auditable, idempotent, and safe under retries or concurrent requests.
**Depends on**: Phase 3
**Requirements**: WAL-01, WAL-02, WAL-03, WAL-04, WAL-05, WAL-06, WAL-07, TEST-03
**Success Criteria** (what must be TRUE):
  1. User can fetch wallet balance from the backend, and the value matches the append-only transaction history.
  2. Backend records every coin grant, debit, refund, and adjustment as a transaction row that can be audited.
  3. Backend blocks billable generation when balance is insufficient and returns a clear error code, using server-controlled pricing of 20 coins for full pages and 4 coins for scene regeneration.
  4. Duplicate or retried requests with the same idempotency key return one logical result and do not double-charge the user.
  5. Concurrent wallet operations cannot create negative balances, and automated tests cover ledger correctness, insufficient balance, idempotency, no-debit/refund failure paths, and concurrent debit protection.
**Plans**: TBD

### Phase 5: Private Comic Persistence
**Goal**: Authenticated users can create, save, reopen, and continue private comics that belong only to them.
**Depends on**: Phase 4
**Requirements**: COMIC-01, COMIC-02, COMIC-03, COMIC-04, COMIC-05, COMIC-06, TEST-04
**Success Criteria** (what must be TRUE):
  1. User can create a private comic draft with title, story, characters, style, tone, selected model, and status.
  2. User can save and reload comic scenes and pages with stable order, editable text fields, generation status, model, cost, image location, and timestamps.
  3. User can list their own comics and open one by id.
  4. User cannot list, open, update, or generate pages for another user's comics.
  5. Browser refresh or reopening a comic restores persisted draft metadata, scenes, and generated page records, with tests proving two-user ownership boundaries.
**Plans**: TBD

### Phase 6: Production AI Generation Pipeline
**Goal**: Authenticated AI generation produces durable comic page records, controlled image assets, correct job states, and updated balance/page data.
**Depends on**: Phase 5
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06, GEN-07, TEST-05
**Success Criteria** (what must be TRUE):
  1. Authenticated user can generate a comic page through the backend using the existing creator payload shape or a documented migration-compatible replacement.
  2. Successful page generation stores durable page metadata and copies the generated image to controlled object storage or an equivalent durable storage layer before returning success.
  3. Generation failure leaves a persisted failed status and does not incorrectly spend coins.
  4. OpenRouter calls use timeout handling, safe retry/error mapping, model allow-list validation, and fixture-backed response parsing; AI text assistance remains available with validation, auth/rate-limit protection, and no client-side provider secrets.
  5. Generation responses return updated balance plus persisted page/comic data needed by the frontend, and tests cover OpenRouter parsing and failure modes with fixtures.
**Plans**: TBD

### Phase 7: Creator Frontend Backend Integration
**Goal**: The existing static creator visibly uses authenticated backend truth for profile, balance, comic history, and generation results instead of demo-only browser state.
**Depends on**: Phase 6
**Requirements**: PROF-04, TEST-06
**Success Criteria** (what must be TRUE):
  1. User opening the creator shell sees authenticated backend account/profile data and wallet balance instead of demo profile data and hardcoded credits.
  2. User can list, open, reload, and continue persisted comics through the existing static creator experience.
  3. Generation UI consumes backend responses for updated balance and persisted page/comic data, with demo-only credit, profile, and logout paths removed or replaced.
  4. Manual or automated smoke checks cover sign-in, profile display, balance display, comic creation, page generation, reload/reopen, and logout.
**Plans**: TBD
**UI hint**: yes

### Phase 8: Deployment And Operations
**Goal**: The production backend can be configured, deployed, documented, and smoke-tested with secure operational defaults.
**Depends on**: Phase 7
**Requirements**: OPS-01, OPS-02, OPS-03, OPS-04, OPS-05
**Success Criteria** (what must be TRUE):
  1. Project includes `.env.example` documenting required local and production environment variables.
  2. Developer can follow local setup instructions for install, migrations, tests, and server startup.
  3. Developer can follow production deployment instructions covering database, storage, OAuth callback, cookie, and environment configuration.
  4. Production deployment serves the app, connects to production database/storage, and supports Google/Yandex OAuth on the production domain.
  5. Auth, generation, profile writes, and other sensitive endpoints have basic rate limiting and security headers in the production deployment.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Foundation And Static Safety | 3/3 | Complete | 2026-04-26 |
| 2. Data And Payment Foundation | 3/3 | Complete | 2026-04-26 |
| 3. OAuth Sessions And Profile Bootstrap | 4/4 | Complete | 2026-04-27 |
| 4. Wallet Ledger And Coin Safety | 0/TBD | Not started | - |
| 5. Private Comic Persistence | 0/TBD | Not started | - |
| 6. Production AI Generation Pipeline | 0/TBD | Not started | - |
| 7. Creator Frontend Backend Integration | 0/TBD | Not started | - |
| 8. Deployment And Operations | 0/TBD | Not started | - |
