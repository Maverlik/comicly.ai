# Requirements: Comicly.ai

**Defined:** 2026-04-25
**Core Value:** Users can reliably create AI-generated comic pages under their own account, with durable comic history and trustworthy server-side coin accounting.

## v1 Requirements

Requirements for the initial production backend milestone. Each maps to one roadmap phase.

### Backend Foundation

- [x] **SAFE-01**: Static serving only exposes intended public application files and assets, not `.env`, `.planning/`, `backend/`, package metadata, or other private repository files.
- [x] **SAFE-02**: Server code is split into clear backend modules for app setup, config, routes, middleware, services, storage, and database access while preserving `npm start`.
- [x] **SAFE-03**: JSON APIs return consistent error responses with stable machine-readable error codes.
- [x] **SAFE-04**: Backend validates request bodies, query parameters, and route parameters before business logic runs.
- [x] **SAFE-05**: Existing AI route contracts remain available during migration: `GET /api/health`, `POST /api/ai-text`, and `POST /api/generate-comic-page`.

### Data Model

- [x] **DATA-01**: Developer can run database migrations from a clean checkout to create all production backend tables.
- [x] **DATA-02**: Database stores users, OAuth provider identities, profiles, sessions, wallets, wallet transactions, comics, comic scenes, comic pages, generation jobs, coin packages, and payment placeholders.
- [x] **DATA-03**: Database constraints prevent duplicate provider identities, duplicate idempotency keys, invalid wallet balances, and cross-owner comic/page relationships.
- [x] **DATA-04**: Seed data creates active coin packages for 100, 500, and 1000 coins.
- [x] **DATA-05**: Runtime configuration defines generation costs and starter coins without scattering hardcoded prices through frontend and backend code.

### Authentication

- [x] **AUTH-01**: User can sign in with Google OAuth and receive a secure server-side session.
- [x] **AUTH-02**: User can sign in with Yandex OAuth and receive a secure server-side session.
- [x] **AUTH-03**: First OAuth login creates the user, provider identity, profile, wallet, and starter coin ledger entry.
- [x] **AUTH-04**: Returning OAuth login attaches to the existing user by provider and provider user id.
- [x] **AUTH-05**: User can log out, and the server invalidates the session.
- [x] **AUTH-06**: Private APIs reject anonymous requests and never trust user identity supplied by the browser.
- [x] **AUTH-07**: Session cookies are `HttpOnly`, production `Secure`, and use an appropriate `SameSite` policy.

### Profile And Bootstrap

- [x] **PROF-01**: User can fetch current account, profile, and wallet summary through an authenticated bootstrap API.
- [x] **PROF-02**: User can update display name through an authenticated API and see it persist after reload.
- [ ] **PROF-03**: User can upload or replace an avatar with file type and size validation.
- [ ] **PROF-04**: Frontend creator shell replaces demo profile data and hardcoded credit display with authenticated backend data.

### Wallet And Coins

- [ ] **WAL-01**: User can fetch wallet balance from the backend, and the balance matches transaction history.
- [ ] **WAL-02**: Backend records every coin grant, debit, refund, and adjustment as an append-only transaction row.
- [ ] **WAL-03**: Backend blocks generation when the authenticated user has insufficient coins and returns a clear error code.
- [ ] **WAL-04**: Full comic page generation costs 20 coins through backend-controlled pricing.
- [ ] **WAL-05**: Scene regeneration costs 4 coins through backend-controlled pricing.
- [ ] **WAL-06**: Duplicate or retried requests using the same idempotency key do not double-charge the user.
- [ ] **WAL-07**: Wallet operations cannot produce negative balances under concurrent requests.

### Comic Persistence

- [ ] **COMIC-01**: User can create a private comic draft with title, story, characters, style, tone, selected model, and status.
- [ ] **COMIC-02**: User can save and reload comic scenes with title, description, dialogue, caption, and order.
- [ ] **COMIC-03**: User can save and reload comic pages with page number, generation status, model, cost, image location, and timestamps.
- [ ] **COMIC-04**: User can list their own comics and open one by id.
- [ ] **COMIC-05**: User cannot list, open, update, or generate pages for another user's comics.
- [ ] **COMIC-06**: Browser refresh or reopening a comic restores persisted draft metadata, scenes, and generated pages.

### AI Generation

- [ ] **GEN-01**: Authenticated user can generate a comic page through the backend using the existing creator payload shape or a documented migration-compatible replacement.
- [ ] **GEN-02**: Successful page generation stores durable page metadata and image location before returning the result to the frontend.
- [ ] **GEN-03**: Generated images are copied to controlled object storage or an equivalent durable storage layer rather than relying only on provider URLs or browser memory.
- [ ] **GEN-04**: Generation failure leaves a persisted failure status and does not incorrectly spend coins.
- [ ] **GEN-05**: OpenRouter calls have timeout, retry/error handling, model allow-list validation, and fixture-backed response parsing.
- [ ] **GEN-06**: AI text assistance remains available through backend routes with validation, auth/rate-limit protection, and no provider secrets in client code.
- [ ] **GEN-07**: Generation responses return updated balance and persisted page/comic data needed by the frontend.

### Payment Preparation

- [x] **PAY-01**: User can fetch active coin package catalog from the backend.
- [x] **PAY-02**: Database includes payment placeholder records with status, user, package, amount, currency, and external provider fields.
- [x] **PAY-03**: Payment schema can support future provider webhook idempotency without redesigning wallet or package tables.

### Deployment And Operations

- [ ] **OPS-01**: Project includes `.env.example` documenting required local and production environment variables.
- [ ] **OPS-02**: Project includes local setup instructions for install, migrations, tests, and server startup.
- [ ] **OPS-03**: Project includes production deployment instructions with database, storage, OAuth callback, cookie, and environment configuration.
- [ ] **OPS-04**: Production deployment serves the app, connects to production database/storage, and supports Google/Yandex OAuth on the production domain.
- [ ] **OPS-05**: Auth, generation, profile writes, and other sensitive endpoints have basic rate limiting and security headers.
- [x] **OPS-06**: Public health/readiness behavior is production-safe and does not expose secret/config details.

### Verification

- [x] **TEST-01**: Automated tests cover static file safety, traversal/dotfile denial, API error format, and existing AI route compatibility.
- [x] **TEST-02**: Automated tests cover OAuth/session behavior using mocked providers or callback fixtures.
- [ ] **TEST-03**: Automated tests cover wallet ledger correctness, insufficient balance, idempotency, refunds/no-debit on failure, and concurrent debit protection.
- [ ] **TEST-04**: Automated tests cover comic ownership boundaries with at least two users.
- [ ] **TEST-05**: Automated tests cover OpenRouter response parsing and generation failure modes using fixtures.
- [ ] **TEST-06**: Manual or automated smoke checks cover sign-in, profile display, balance display, comic creation, page generation, reload/reopen, and logout.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Payments

- **PAY-04**: User can complete checkout with a real payment provider.
- **PAY-05**: Payment provider webhook grants purchased coins after verified successful payment.
- **PAY-06**: User can view payment history.

### Product And Community

- **SOC-01**: User can publish a comic to a public gallery.
- **SOC-02**: User can view public profiles.
- **SOC-03**: User can share public comic pages with social metadata.
- **ADM-01**: Admin can review users, payments, and generated comics.
- **NOTF-01**: User receives email or in-app notifications for relevant account events.

### Frontend Evolution

- **UI-01**: Creator frontend can migrate to a component framework if static JavaScript becomes a bottleneck.
- **UI-02**: User can manage a richer model marketplace with dynamic model pricing.
- **UI-03**: User can collaborate with another user on a comic.

## Out of Scope

Explicitly excluded from v1. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real payment-provider checkout and webhooks | v1 only prepares payment-ready database structures and package catalog. |
| Admin panel | Not required to prove user auth, wallet, generation, and private comic history. |
| Role system | Single authenticated user ownership model is enough for v1. |
| Password login | v1 requires Google and Yandex OAuth only. |
| Public profiles and public comic feed | v1 comic history is private per authenticated owner. |
| Social features such as likes, comments, follows, and collaboration | These add authorization and product complexity unrelated to the backend trust milestone. |
| Email campaigns or notification emails | No v1 flow depends on email delivery. |
| Full frontend framework rewrite | Current static frontend should be preserved unless a later phase validates migration need. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SAFE-01 | Phase 1 | Complete in 01-03 |
| SAFE-02 | Phase 1 | Complete in 01-01 |
| SAFE-03 | Phase 1 | Complete in 01-01 |
| SAFE-04 | Phase 1 | Complete in 01-01 |
| SAFE-05 | Phase 1 | Complete in 01-03 |
| DATA-01 | Phase 2 | Complete in 02-02 |
| DATA-02 | Phase 2 | Complete in 02-01/02-02 |
| DATA-03 | Phase 2 | Complete in 02-02 |
| DATA-04 | Phase 2 | Complete in 02-03 |
| DATA-05 | Phase 2 | Complete in 02-01/02-03 |
| AUTH-01 | Phase 3 | Complete in 03-02 |
| AUTH-02 | Phase 3 | Complete in 03-02 |
| AUTH-03 | Phase 3 | Complete in 03-02 |
| AUTH-04 | Phase 3 | Complete in 03-02 |
| AUTH-05 | Phase 3 | Complete in 03-03 |
| AUTH-06 | Phase 3 | Complete in 03-03 |
| AUTH-07 | Phase 3 | Complete in 03-01 |
| PROF-01 | Phase 3 | Complete in 03-03 |
| PROF-02 | Phase 3 | Complete in 03-03 |
| PROF-03 | Deferred | Pending storage provider decision |
| PROF-04 | Phase 7 | Pending |
| WAL-01 | Phase 4 | Pending |
| WAL-02 | Phase 4 | Pending |
| WAL-03 | Phase 4 | Pending |
| WAL-04 | Phase 4 | Pending |
| WAL-05 | Phase 4 | Pending |
| WAL-06 | Phase 4 | Pending |
| WAL-07 | Phase 4 | Pending |
| COMIC-01 | Phase 5 | Pending |
| COMIC-02 | Phase 5 | Pending |
| COMIC-03 | Phase 5 | Pending |
| COMIC-04 | Phase 5 | Pending |
| COMIC-05 | Phase 5 | Pending |
| COMIC-06 | Phase 5 | Pending |
| GEN-01 | Phase 6 | Pending |
| GEN-02 | Phase 6 | Pending |
| GEN-03 | Phase 6 | Pending |
| GEN-04 | Phase 6 | Pending |
| GEN-05 | Phase 6 | Pending |
| GEN-06 | Phase 6 | Pending |
| GEN-07 | Phase 6 | Pending |
| PAY-01 | Phase 2 | Complete in 02-03 |
| PAY-02 | Phase 2 | Complete in 02-02 |
| PAY-03 | Phase 2 | Complete in 02-02 |
| OPS-01 | Phase 8 | Pending |
| OPS-02 | Phase 8 | Pending |
| OPS-03 | Phase 8 | Pending |
| OPS-04 | Phase 8 | Pending |
| OPS-05 | Phase 8 | Pending |
| OPS-06 | Phase 1 | Complete in 01-02 |
| TEST-01 | Phase 1 | Complete in 01-03 |
| TEST-02 | Phase 3 | Complete in 03-04 |
| TEST-03 | Phase 4 | Pending |
| TEST-04 | Phase 5 | Pending |
| TEST-05 | Phase 6 | Pending |
| TEST-06 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 56 total
- Mapped to phases: 56
- Unmapped: 0
- Coverage: 100%

---
*Requirements defined: 2026-04-25*
*Last updated: 2026-04-27 after Phase 3 verification*
