# Architecture Research: Production Backend Evolution

**Project:** Comicly.ai
**Dimension:** Architecture
**Researched:** 2026-04-25
**Confidence:** HIGH for current-code constraints; MEDIUM for deployment details until final host/database choices are locked.

## Executive Recommendation

Comicly.ai should evolve from the current single `server.js` into a modular Node backend that still serves the existing static frontend, but treats API, auth, persistence, wallet accounting, generation, and static delivery as separate boundaries. Do not rewrite the frontend or replace the AI routes first. The safest migration is to preserve `/api/ai-text` and `/api/generate-comic-page` response contracts while moving implementation behind production services.

The production backend should be a backend-for-frontend plus worker-capable API service:

```text
Browser static UI
  -> HTTP API router
    -> session/auth boundary
    -> validation/idempotency/rate-limit boundary
    -> domain services
      -> users/profiles
      -> wallet ledger
      -> comics/pages
      -> generation jobs
      -> payment preparation
    -> infrastructure adapters
      -> database
      -> object storage
      -> OpenRouter
      -> static public-file server
```

The critical architectural change is trust ownership. The browser may hold draft editing state, but it must not own identity, coin balance, debit decisions, generated-page ownership, or permanent comic history. Those must move to database-backed server components before production exposure.

## Current Architecture Constraints

| Current behavior | Production risk | Migration implication |
|------------------|-----------------|-----------------------|
| `server.js` combines env loading, routing, static serving, OpenRouter, prompt logic, and health | Auth, persistence, wallet, and deployment changes all collide in one file | Split by boundary before adding feature depth |
| Static serving uses repository root | `.env`, `.planning/`, `backend/`, and package files can be exposed | Move public assets to explicit allowlist or `public/` root early |
| `/api/generate-comic-page` is synchronous and unauthenticated | Anyone can spend OpenRouter quota and requests can hang | Add auth, rate limits, idempotency, and later job status |
| `credits` lives in `scripts/creator.js` | Client can bypass billing | Wallet service and DB transaction log become source of truth |
| Comic pages live in browser memory or external returned URLs | Refresh loses work; external URLs may expire | Store comic/page rows and copy generated images to object storage |
| `GET /api/health` exposes config details | Operational metadata leaks publicly | Keep public health minimal; move diagnostics behind auth or logs |

## Target Backend Components

### 1. HTTP App Shell

**Responsibility:** Own process startup, config loading, HTTP server creation, global error handling, request IDs, security headers, and graceful shutdown.

**Recommended files:**

```text
server.js                 # thin entrypoint, starts app
server/app.js             # creates HTTP app/router
server/config.js          # env parsing and typed config
server/http/respond.js    # JSON/static response helpers
server/http/errors.js     # normalized API errors
```

**Boundary rule:** `server.js` should stop knowing about OpenRouter prompts, wallet math, OAuth, or database SQL. It should only load config, create the app, and listen.

### 2. Router and Middleware Layer

**Responsibility:** Dispatch route groups, parse request bodies, attach request context, enforce auth where needed, and apply rate limits.

**Recommended route groups:**

```text
server/routes/health.routes.js
server/routes/auth.routes.js
server/routes/me.routes.js
server/routes/wallet.routes.js
server/routes/comics.routes.js
server/routes/generation.routes.js
server/routes/payments.routes.js
```

**Middleware order:**

1. Request ID and structured log context.
2. Security headers.
3. Static deny rules or public static serving.
4. Body size/content-type validation for API routes.
5. Session loading from `HttpOnly` cookie.
6. CSRF protection for cookie-authenticated mutating routes.
7. Rate limiting by IP, then by user for authenticated routes.
8. Route handler.
9. Normalized error response.

**Migration constraint:** Keep the legacy endpoints during frontend migration:

| Legacy route | New internal owner | Compatibility plan |
|--------------|--------------------|--------------------|
| `POST /api/ai-text` | generation/text service | Require auth once login exists; keep response shape `{ text, model }` / `{ scenes, model }` |
| `POST /api/generate-comic-page` | generation job service | First wrap with wallet debit and persistence; later return job status if async migration is needed |
| `GET /api/health` | health route | Return only `{ ok: true }` publicly |

### 3. Authentication and Session Service

**Responsibility:** OAuth with Google/Yandex, provider identity linking, server-side session creation, session lookup, logout, and current-user API.

**Core tables:**

```text
users
provider_accounts
sessions
profiles
```

**Component boundary:**

```text
auth.routes
  -> oauthProviderClient
  -> authService
    -> usersRepository
    -> providerAccountsRepository
    -> sessionsRepository
    -> walletService.createStarterWallet()
```

**Required flows:**

1. `GET /api/auth/:provider/start` creates OAuth state/PKCE data, stores it server-side, redirects to provider.
2. `GET /api/auth/:provider/callback` validates state, exchanges code server-side, fetches provider identity, creates or finds `users` and `provider_accounts`, ensures profile and wallet exist, creates `sessions`, sets cookie.
3. `POST /api/auth/logout` deletes the session row and clears the cookie.
4. `GET /api/me` returns user/profile/balance from server state.

**Cookie policy:**

Use `HttpOnly`, `Secure` in production, `SameSite=Lax`, short enough expiry for product risk, and rotating opaque session IDs. Do not store provider access tokens in browser-accessible state.

### 4. Persistence Layer

**Responsibility:** Isolate database access behind repositories and migrations. All private data and balances must come from the database.

**Recommended model groups:**

| Domain | Tables | Notes |
|--------|--------|-------|
| Identity | `users`, `provider_accounts`, `sessions` | Provider identity is keyed by `(provider, provider_user_id)` |
| Profile | `profiles` | Display name and avatar object key/URL |
| Wallet | `wallets`, `wallet_transactions`, `idempotency_keys` | Ledger is authoritative; balance must match ledger |
| Comics | `comics`, `comic_pages`, `comic_scenes` | Store drafts, metadata, generated pages, page order, statuses |
| Generation | `generation_jobs` | Persist request, cost, status, prompt version, provider response metadata |
| Payments prep | `coin_packages`, `payments` | Seed 100/500/1000 packages; no real webhook yet |

**Repository boundary:**

Repositories should expose intent-specific operations rather than generic SQL from route handlers:

```text
walletRepository.debitForGeneration({ userId, amount, idempotencyKey, reason, jobId })
comicRepository.upsertDraftFromGenerationRequest(...)
generationRepository.createQueuedJob(...)
generationRepository.markSucceeded(...)
generationRepository.markFailed(...)
```

### 5. Wallet and Transaction Service

**Responsibility:** Own every balance read, debit, credit, refund, and transaction-log write.

**Rules:**

- Browser-supplied balance is ignored.
- Debit is atomic and guarded by current balance.
- Every balance change writes a `wallet_transactions` row.
- Idempotency key prevents double debit on retry/double click.
- Generation failure either avoids debit until success or records an automatic refund in the same recovery path.

**Recommended first implementation: debit on successful generation.**

For the current synchronous route, avoid charging before OpenRouter succeeds. The flow is:

1. Validate authenticated user and payload.
2. Check current balance is at least generation cost.
3. Call OpenRouter.
4. Persist generated page/image.
5. In one DB transaction: create/update comic/page, insert wallet debit transaction, update wallet balance, link transaction to page/job.
6. Return page data and updated balance.

This avoids refunds in the first milestone. It still needs idempotency because the same successful OpenRouter response must not be charged twice on retry. If the architecture moves to queued jobs, switch to reserve/debit/refund states.

### 6. Generation Service and Jobs

**Responsibility:** Own AI text/page generation, prompt templates, model allowlist, provider adapters, output validation, storage copy, and job state.

**Recommended files:**

```text
server/generation/generationService.js
server/generation/textTasks.js
server/generation/promptTemplates.js
server/generation/modelRegistry.js
server/generation/openRouterClient.js
server/generation/imageStorage.js
```

**Model registry:**

Move `DEFAULT_IMAGE_MODEL`, `DEFAULT_TEXT_MODEL`, and `ALLOWED_IMAGE_MODELS` into one backend registry. Expose only safe metadata to the browser:

```text
GET /api/generation/models
  -> [{ id, label, supportsText, costCoins, enabled }]
```

**Prompt versioning:**

Each generated page should store `prompt_version`, `model_id`, normalized payload, and output metadata. This is needed for debugging, replay, and future quality changes.

**Job states:**

Use even if the first route remains synchronous:

```text
created -> running -> succeeded
created -> running -> failed
created -> canceled
```

**Synchronous-to-async migration path:**

Phase 1 can keep `POST /api/generate-comic-page` open until generation completes. Internally it still creates a `generation_jobs` row.

Phase 2 can change the frontend to:

```text
POST /api/generation/jobs -> { jobId }
GET /api/generation/jobs/:jobId -> { status, page, balance }
```

The existing route can remain a compatibility wrapper around the job API until the frontend no longer uses it.

### 7. Comics and Pages Service

**Responsibility:** Persist user-owned comic drafts, story metadata, scenes, generated page records, and page history.

**APIs:**

```text
GET    /api/comics
POST   /api/comics
GET    /api/comics/:comicId
PATCH  /api/comics/:comicId
POST   /api/comics/:comicId/pages
PATCH  /api/comics/:comicId/pages/:pageId
DELETE /api/comics/:comicId
```

**Ownership rule:** Every comic/page query includes `user_id = currentUser.id`. Route handlers must not fetch a comic by ID alone.

**Draft rule:** Browser state can remain fast and local while editing, but every explicit save/generation should upsert server-side comic metadata: title, story, characters, style, tone, scenes, page order, and active page payload.

### 8. Object Storage Boundary

**Responsibility:** Store generated images and uploaded avatars outside the repo and database.

**Rules:**

- Do not trust long-lived availability of provider-returned image URLs.
- Copy successful generated output into object storage before marking a page as `generated`.
- Store object key and public/signed URL metadata in `comic_pages`.
- Validate URL/data URL scheme before ingesting provider output.
- Avatar upload validates content type, size, and dimensions before storage.

**Local development:** Use a local storage adapter writing under an ignored directory such as `.data/uploads/`, but never serve that directory through repository-root static serving.

### 9. Payment Preparation Boundary

**Responsibility:** Prepare the data model for future coin purchases without implementing acquiring/webhooks now.

**Tables:**

```text
coin_packages(id, coin_amount, price_amount, currency, active, sort_order)
payments(id, user_id, package_id, status, provider, provider_payment_id, amount, currency, metadata)
```

**API now:**

```text
GET /api/coin-packages
```

**Avoid now:** Any fake successful payment endpoint that credits coins without a provider or admin boundary. Seed packages only.

### 10. Static Serving Safety Component

**Responsibility:** Serve only public runtime files and apply browser security headers.

**Required change before production:**

Replace repository-root file serving with either:

1. A `public/` directory containing only `index.html`, `create.html`, CSS, JS, and assets; or
2. An explicit allowlist map for the current root files.

**Minimum deny rules if keeping current layout temporarily:**

```text
deny dotfiles
deny .planning/
deny backend/
deny package.json and lockfiles
deny server files
deny unknown extensions
deny decoded traversal and absolute paths
```

**Path containment rule:**

Use `path.resolve(publicDir, relativePath)` and accept only:

```text
resolved === publicDir || resolved.startsWith(publicDir + path.sep)
```

Do not rely on raw string prefix checks against the repository root.

**Headers:**

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Strict-Transport-Security` in production
- `Cache-Control` with immutable caching for versioned assets and no-store for HTML/API responses

## Data Flow

### Login Flow

```text
Browser
  -> GET /api/auth/google/start
Backend
  -> create oauth state/PKCE
  -> redirect provider
Provider
  -> callback with code/state
Backend
  -> validate state
  -> exchange code server-side
  -> fetch provider identity
  -> upsert user/provider/profile
  -> create wallet if first login
  -> create session
  -> set HttpOnly cookie
Browser
  -> GET /api/me
  -> render real profile and balance
```

### Current User Bootstrap

```text
create.html loads
  -> scripts/creator.js calls GET /api/me
  -> if 200: render profile, balance, history links
  -> if 401: render login state and block generation
```

The frontend should stop initializing a trusted `credits = 240`. It may render a loading or signed-out state until `/api/me` returns.

### Text Generation Flow

```text
Browser
  -> POST /api/ai-text { task, story, scene fields }
API router
  -> require session
  -> validate task and bounded text fields
  -> rate limit
generationService
  -> choose prompt template/version
  -> call OpenRouter through adapter with timeout
  -> parse/validate text or scenes JSON
Response
  -> { text/scenes, model }
```

Text assist may remain free initially, but it still needs auth and rate limits because it spends provider quota.

### Comic Page Generation Flow: First Production Version

```text
Browser
  -> POST /api/generate-comic-page
     { comicId?, idempotencyKey, story, characters, scenes, page, model, style, tone }
API router
  -> require session
  -> validate body and idempotency key
  -> check rate limit
walletService
  -> confirm balance >= cost without mutating yet
generationService
  -> create generation_jobs row: running
  -> call OpenRouter with timeout
  -> validate image output
imageStorage
  -> copy generated image to object storage
database transaction
  -> upsert comic draft
  -> upsert comic page
  -> mark generation job succeeded
  -> debit wallet
  -> insert wallet transaction
Response
  -> { page, imageUrl, model, balance, transactionId, jobId }
```

If OpenRouter or storage fails before the DB transaction, no debit is written. If the DB transaction fails after provider success, the job should be marked recoverable in logs and retried manually or by worker tooling; do not report success to the user without persisted page and debit consistency.

### Queued Generation Flow: Later Version

```text
POST /api/generation/jobs
  -> validate/auth/idempotency
  -> reserve coins or verify balance
  -> create queued job
  -> return { jobId }

Worker
  -> claim queued job
  -> call OpenRouter
  -> store image
  -> commit page and debit/finalize reservation
  -> mark succeeded or failed/refunded

GET /api/generation/jobs/:jobId
  -> return status, page, balance
```

This is the right long-term design because image generation is slow and failure-prone, but the first production milestone can defer an external queue if the code still persists `generation_jobs` and uses timeouts.

### Comic History Flow

```text
GET /api/comics
  -> session user id
  -> list only comics where user_id = current user
  -> include cover page thumbnail, status, updated_at

GET /api/comics/:id
  -> session user id
  -> fetch comic by id and user_id
  -> fetch pages/scenes in stable order
  -> frontend restores editor state from server data
```

## Build Order

### Phase 1: Safety and Module Extraction

**Goal:** Create backend seams without changing user-visible behavior.

1. Extract config/env, response helpers, OpenRouter client, prompt builders, and route handlers from `server.js`.
2. Add request body validation helpers and route-level error normalization.
3. Replace repository-root static serving with an explicit public directory or allowlist.
4. Add security headers and fix `HEAD` handling.
5. Keep `/api/ai-text`, `/api/generate-comic-page`, and `/api/health` behavior compatible.

**Why first:** Static file exposure and single-file coupling are immediate production blockers. This phase reduces risk before adding auth and money.

### Phase 2: Database Foundation

**Goal:** Add migrations, repositories, and seed data with no frontend dependency yet.

1. Add database connection and migration runner.
2. Create identity, profile, wallet, comic, generation, package, and payment tables.
3. Seed coin packages `100`, `500`, and `1000`.
4. Seed or configure generation costs: full page `20`, scene regeneration `4`.
5. Add repository tests for wallet and ownership queries.

**Why second:** Auth, wallet, and comic APIs all depend on durable schema.

### Phase 3: Auth and Current User

**Goal:** Replace demo identity with real sessions.

1. Implement Google OAuth.
2. Implement Yandex OAuth.
3. Add session middleware and logout.
4. Add `GET /api/me` and profile update API.
5. Update frontend profile/balance bootstrap to use backend data.

**Why third:** Private comics and wallet operations need authenticated ownership before being exposed.

### Phase 4: Wallet Ledger

**Goal:** Make coins authoritative on the backend.

1. Implement wallet creation on first login.
2. Implement balance read from DB.
3. Implement atomic debit/credit transaction methods.
4. Add idempotency table and duplicate-request behavior.
5. Add insufficient-balance response codes and frontend handling.

**Why fourth:** Generation must not become billable until debit correctness is tested.

### Phase 5: Comic Persistence

**Goal:** Save and reopen user-owned comics.

1. Add comics/pages/scenes APIs.
2. Persist generated pages and editor metadata.
3. Add list/reopen flow to the static creator frontend.
4. Enforce user ownership on every comic/page query.

**Why fifth:** This can be built safely once identity and DB ownership exist.

### Phase 6: Production Generation Transactions

**Goal:** Connect generation, persistence, and wallet into one coherent workflow.

1. Wrap existing generation route with session, validation, idempotency, and balance checks.
2. Create `generation_jobs` rows for every page generation.
3. Copy generated image output to object storage.
4. Commit page persistence and wallet debit in one DB transaction.
5. Return updated balance and page record to the frontend.

**Why sixth:** This is where money and AI cost meet. It depends on the previous boundaries being real.

### Phase 7: Deployment and Operations

**Goal:** Make the system repeatable in production.

1. Document required env variables.
2. Configure production host, database, object storage, and OAuth redirect URIs.
3. Add logs, request IDs, OpenRouter timeouts, and health/readiness checks.
4. Add smoke tests for static safety, auth callback, wallet debit, insufficient balance, and comic ownership.

**Why last:** Deployment can start earlier, but final production acceptance requires all security and data flows to exist.

## Migration Constraints

### Preserve Existing Static Frontend

Do not introduce a framework migration as part of this backend architecture. `index.html`, `create.html`, `styles.css`, `creator.css`, `scripts/main.js`, and `scripts/creator.js` can stay static. Add a small frontend API client module only if it reduces duplication.

### Preserve AI Route Contracts Initially

The existing creator currently expects:

```text
POST /api/ai-text -> { text, model } or { scenes, model }
POST /api/generate-comic-page -> { imageUrl, model, text }
```

Production responses may add fields such as `balance`, `page`, `jobId`, and `transactionId`, but should not remove existing fields until the frontend is migrated.

### Do Not Trust Client Credits

Remove or downgrade client `credits` to display-only state populated from `/api/me` and generation responses. The server decides whether a user can generate.

### Do Not Serve From Repository Root

This is a hard production constraint. Even if the backend remains small, production static serving must be limited to public files. Repository-root serving should be considered local-demo only.

### Avoid Long-Lived External Image URLs

Persist the generated page record only after copying image output into controlled storage. OpenRouter response URLs/data URLs are provider output, not the durable Comicly.ai asset.

### Keep Payment Tables Passive

Payment tables and coin package APIs should exist, but no endpoint should credit purchased coins until a real provider/webhook or admin-safe path is implemented.

### Add Tests Around Boundaries, Not Implementation Details

Minimum architecture tests:

| Area | Test |
|------|------|
| Static safety | `.env`, `.planning/`, `backend/`, `package.json`, traversal, and unknown extensions are denied |
| Auth | invalid state fails, callback creates user/session, logout clears session |
| Wallet | debit is atomic, insufficient balance fails, duplicate idempotency key does not double charge |
| Generation | OpenRouter failure does not debit, success persists page and debits once |
| Ownership | user cannot read/update another user's comic |
| Health | public health does not leak model IDs or key presence |

## Recommended Component Boundaries

| Component | Owns | Must not own |
|-----------|------|--------------|
| `app/server` | startup, config, global middleware | business rules |
| `routes` | HTTP mapping and request/response shape | SQL, provider-specific logic |
| `authService` | OAuth, sessions, current user | wallet debits, comic generation |
| `walletService` | balance, ledger, idempotency, refunds | OpenRouter prompts |
| `comicService` | comic/page ownership and persistence | coin math |
| `generationService` | prompts, models, jobs, provider output | session cookies |
| `openRouterClient` | provider HTTP calls and response adapters | route validation or wallet logic |
| `storageService` | avatars and generated image storage | comic ownership decisions |
| `repositories` | database access | HTTP response construction |
| `staticServer` | public files and headers | API route fallback |

## Suggested Directory Shape

```text
server.js
server/
  app.js
  config.js
  http/
    errors.js
    respond.js
    router.js
    securityHeaders.js
    staticServer.js
  middleware/
    requireSession.js
    rateLimit.js
    csrf.js
    requestId.js
  auth/
    auth.routes.js
    authService.js
    oauthProviders.js
    sessionService.js
  users/
    me.routes.js
    profileService.js
  wallet/
    wallet.routes.js
    walletService.js
  comics/
    comics.routes.js
    comicService.js
  generation/
    generation.routes.js
    generationService.js
    textTasks.js
    promptTemplates.js
    modelRegistry.js
    openRouterClient.js
  payments/
    payments.routes.js
    packageService.js
  db/
    connection.js
    migrations/
    repositories/
  storage/
    storageService.js
    localStorageAdapter.js
```

If the project deliberately stays dependency-light, this shape can still use Node core modules. If backend complexity accelerates, adding a small HTTP framework is acceptable, but the more important decision is the component boundary, not the router library.

## Architecture Decisions for Roadmap

1. Build static-serving safety before auth. Auth cookies and secrets make root static serving more dangerous, not less.
2. Build database and migrations before OAuth completion. First login must create users, provider identities, profiles, sessions, and wallets transactionally.
3. Build wallet before paid generation. The AI route should not debit until ledger correctness and idempotency are tested.
4. Persist generation jobs even while requests remain synchronous. This creates the future async migration path without forcing frontend polling immediately.
5. Treat object storage as part of generation success. A generated page is not durable until Comicly.ai controls the image asset.
6. Keep payment integration out of scope but payment schema in scope. This avoids rebuilding wallet tables when purchases arrive later.

## Open Questions

| Question | Impact | Recommendation |
|----------|--------|----------------|
| Final database provider | Affects migrations, transaction syntax, deployment | Choose one before Phase 2; PostgreSQL is the safest default for wallet transactions |
| Final object storage provider | Affects avatar/page URL strategy | Use an adapter interface so local storage and production storage differ only by config |
| Router/framework choice | Affects implementation style | Keep Node core for extraction if speed matters; introduce a framework only if middleware complexity becomes costly |
| Synchronous vs queued generation in v1 | Affects frontend loading state | Start synchronous with persisted jobs and timeouts; migrate to polling when generation duration hurts UX |
| Starter coin amount | Affects first-login wallet seed | Keep configurable through `STARTER_COINS` and record seed as a wallet transaction |

