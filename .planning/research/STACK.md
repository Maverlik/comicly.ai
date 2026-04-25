# Stack Research: Production Backend for Comicly.ai

**Project:** Comicly.ai
**Dimension:** Stack and implementation approach
**Researched:** 2026-04-25
**Overall confidence:** HIGH for backend shape, database/auth/session choices; MEDIUM for exact deployment provider until production domain and budget are fixed.

## Recommendation

Use a small Express 5 backend on Node 22, PostgreSQL, Drizzle ORM, Arctic for Google/Yandex OAuth code flow, server-side Postgres-backed sessions, S3-compatible object storage, and Vitest/Supertest tests. Keep `index.html`, `create.html`, `styles.css`, `creator.css`, `scripts/main.js`, `scripts/creator.js`, and `assets/` as static frontend assets. Replace the current `server.js` internals with a modular app while preserving the public OpenRouter-backed route contracts:

- `POST /api/ai-text`
- `POST /api/generate-comic-page`
- `GET /api/health`

The key production change is not a frontend rewrite. It is moving trust boundaries into backend modules: auth, session validation, wallet balance checks, idempotency, ledger transactions, comic persistence, generated image storage, and deployment configuration.

## Recommended Stack

| Area | Recommendation | Why |
|------|----------------|-----|
| Runtime | Node.js 22+ | Already declared in `package.json`; supports native `fetch`, Web Crypto, and modern JS without polyfills. |
| HTTP framework | Express 5 | Lowest-friction replacement for the current `node:http` server; mature middleware ecosystem for sessions, cookies, static serving, rate limiting, security headers, and Vercel deployment. |
| Database | PostgreSQL | Best fit for coin ledger correctness, transactions, row locks, uniqueness constraints, idempotency keys, and future payments. |
| ORM/query layer | Drizzle ORM + `pg` | Lightweight, migration-friendly, SQL-shaped, and easier than Prisma for ledger transactions that need explicit locking and raw SQL escape hatches. |
| Auth OAuth client | `arctic` | Supports OAuth authorization-code clients for Google and Yandex without forcing a full auth framework. Good fit for custom user/profile/wallet creation logic. |
| Sessions | `express-session` + `connect-pg-simple` | Server-side sessions satisfy the requirement that cookies only carry a session id. Postgres session store avoids MemoryStore production issues. |
| Validation | `zod` | Central request validation for auth callbacks, profile updates, generation payloads, comic metadata, pagination, and idempotency headers. |
| Security middleware | `helmet`, `express-rate-limit` | Add security headers and abuse controls around auth, AI routes, profile writes, and generation. |
| Object storage | S3-compatible storage, preferably Cloudflare R2 | Generated images may arrive as base64 data URLs and should not live in Postgres or browser memory. R2 works through AWS SDK v3 and avoids tying the app to one compute host. |
| AI provider | Keep OpenRouter via native `fetch` | Existing routes and provider boundary already work; wrap them in a service with timeout, model registry, response fixtures, and persistence. |
| Testing | Vitest + Supertest + test Postgres | Supertest fits Express route tests. Ledger/idempotency behavior should run against real Postgres, not an in-memory substitute. |
| Deployment | Vercel + Neon Postgres + R2 for first production; Docker/Fly/Render if workers become necessary | Vercel now supports Express and long Node function durations with Fluid Compute. If generation becomes queue/worker-heavy, move backend compute to a long-running host while keeping the static frontend unchanged. |

## Why This Stack

### Express 5 Over Keeping `node:http`

The current `server.js` is useful as a prototype but is already doing too much: env loading, static serving, routing, OpenRouter calls, validation, prompt construction, and health checks. Production auth and billing would make the single-file server brittle.

Express 5 is the conservative upgrade because it can preserve the app's current shape:

- same-origin static frontend and JSON APIs;
- no React/Next.js migration;
- route handlers remain ordinary async functions;
- mature middleware exists for sessions, cookies, secure static serving, rate limits, and tests;
- Vercel officially documents Express deployment.

Tradeoff: Express does not enforce structure. The roadmap should require a module layout and tests from the first backend phase so the code does not become another large single file.

### PostgreSQL + Drizzle Over SQLite, MongoDB, or Prisma

Coins are financial-style state. The database must support atomic balance checks, idempotency, append-only transaction history, uniqueness constraints, and race-condition protection. PostgreSQL is the right baseline.

Use Drizzle because this app needs readable SQL-shaped operations more than a high-level domain ORM. Wallet debit/reserve/refund logic will need explicit transactions and likely `SELECT ... FOR UPDATE` or single-statement conditional updates. Drizzle supports transactions and raw SQL when the query builder is not enough.

Do not use SQLite for production coins. It is fine for local demos but becomes a deployment and concurrency liability once generation requests can run in parallel.

Do not use MongoDB for the ledger. A relational ledger with constraints is simpler and safer.

Do not use Prisma as the first choice here. It is productive for CRUD, but the coin ledger will still need raw SQL and careful transaction handling. Drizzle keeps the schema and SQL closer to what the backend actually needs.

### Arctic Over Auth.js

The app needs Google and Yandex OAuth, no password login, and custom first-login behavior:

1. validate provider callback server-side;
2. upsert `users`;
3. upsert `provider_identities`;
4. create `profiles`;
5. create `wallets`;
6. grant starter coins through the ledger;
7. create a server-side session.

Arctic is a small OAuth client library with Google/Yandex support. It does not own sessions or users, which is an advantage for this brownfield app because wallet creation and starter coin grants must happen in the same application-level flow.

Auth.js is not the recommended first choice for this project because its Express integration is documented as experimental, and its abstractions are more useful when the app wants a full auth framework. Here, the domain logic around profiles, wallets, provider identities, and Yandex makes a smaller OAuth client cleaner.

### Server-Side Sessions Over JWT Auth

Use opaque session ids in `HttpOnly`, `Secure` production cookies with `SameSite=Lax`. Store session data server-side in Postgres.

Reasons:

- logout and revocation are straightforward;
- no trusted balance/profile/session claims live in the browser;
- CSRF and cookie behavior are easier to reason about in a same-origin static app;
- it matches the requirement for secure server-side sessions.

Do not use client-stored JWTs for this milestone. They add token rotation/revocation complexity and encourage trusting browser-held claims.

## Implementation Shape

Create a modular backend under `backend/src/` and leave root `server.js` as the local bootstrap:

```text
server.js                         # local app.listen wrapper, keeps npm start
api/index.js                      # Vercel entrypoint, exports/uses the Express app
backend/src/app.js                # createExpressApp()
backend/src/config.js             # env parsing and required variable validation
backend/src/db/client.js          # pg pool + Drizzle db
backend/src/db/schema.js          # Drizzle table definitions
backend/src/db/migrations/        # generated SQL migrations
backend/src/http/errors.js        # normalized JSON errors
backend/src/http/static.js        # safe static serving
backend/src/http/session.js       # express-session config
backend/src/middleware/auth.js    # requireUser, optionalUser
backend/src/middleware/csrf.js    # same-origin write protection
backend/src/routes/auth.js        # /auth/google, /auth/yandex, callbacks, logout
backend/src/routes/me.js          # profile + wallet summary
backend/src/routes/comics.js      # comic list/detail/create/update
backend/src/routes/generation.js  # ai-text and comic page generation
backend/src/routes/payments.js    # package list, payment-ready tables only
backend/src/routes/health.js      # public minimal health
backend/src/services/openrouter.js
backend/src/services/oauth.js
backend/src/services/wallet.js
backend/src/services/comics.js
backend/src/services/storage.js
backend/src/services/modelRegistry.js
backend/src/services/idempotency.js
backend/src/validation/*.js
backend/tests/**/*.test.js
```

Static frontend options:

1. Preferred: move public files into `public/` during the first backend phase:
   - `public/index.html`
   - `public/create.html`
   - `public/styles.css`
   - `public/creator.css`
   - `public/scripts/*`
   - `public/assets/*`

2. If moving files is too disruptive, serve only an explicit allowlist from repo root and deny dotfiles, `.planning/`, `backend/`, package metadata, and unknown paths. This is a temporary bridge only.

The current root static server can expose `.env`, `.planning/`, and backend docs. Production must not deploy that behavior.

## Database Model

Minimum tables for this milestone:

| Table | Purpose | Notes |
|-------|---------|-------|
| `users` | Stable application user | `id`, timestamps, status. |
| `provider_identities` | Google/Yandex identity links | Unique `(provider, provider_user_id)`, optional email snapshot. |
| `profiles` | Display name and avatar reference | One row per user. Store custom avatar object key, not raw bytes. |
| `sessions` | Server-side sessions | Used by `connect-pg-simple` or compatible custom schema. |
| `wallets` | Current wallet counters | `balance_coins`, optional `reserved_coins`, one row per user. |
| `coin_transactions` | Append-only ledger | Every grant, reserve, spend, refund, adjustment. Include `balance_after`, idempotency key, and reference id. |
| `idempotency_keys` | Retry/double-click protection | Unique per user + operation + key. Stores response or reference to result. |
| `comics` | Private comic projects/history | Story, characters, style, tone, status, owner. |
| `comic_pages` | Generated pages | Page number, prompt metadata, model, cost, object key/image URL, status. |
| `generation_jobs` | AI generation lifecycle | pending/running/succeeded/failed; stores provider request metadata and errors. |
| `coin_packages` | Future payment products | Seed 100, 500, 1000 coin packages. |
| `payments` | Future provider payments | No real acquiring yet; include provider fields and statuses. |

Use integer coin amounts. Do not use floats. Add constraints so balances cannot go negative and package coin amounts are positive.

## Coin Ledger Approach

Use a reserve/commit/refund flow rather than a naive "call OpenRouter then debit" flow.

Recommended generation sequence:

1. Require an authenticated session.
2. Validate payload with Zod.
3. Require an `Idempotency-Key` header for paid generation.
4. In a short DB transaction:
   - lock or conditionally update the user's wallet;
   - verify available balance;
   - reserve/debit the required coins;
   - insert a `coin_transactions` reserve/debit row;
   - insert `generation_jobs` as `pending`;
   - create or update the target `comics` row.
5. Call OpenRouter outside the DB transaction with a timeout.
6. Store the generated image in R2/S3-compatible storage.
7. In a second DB transaction:
   - mark the generation job `succeeded`;
   - insert/update `comic_pages`;
   - convert reserve to spend or finalize the debit;
   - write final ledger row and `balance_after`;
   - store the idempotency result.
8. If OpenRouter/storage fails, mark the job `failed` and refund/release the reserved coins in a DB transaction.

This avoids two bad outcomes: free successful generation when users race requests, and permanent coin loss when the provider fails after a debit.

For the first implementation, a debit-then-refund model is acceptable if every failure path is tested and every debit/refund is in the ledger. A true `reserved_coins` column is cleaner for long generation jobs.

## API Approach

Keep route names stable but make behavior authenticated where costs or private data are involved.

| Route | Production behavior |
|-------|---------------------|
| `GET /api/health` | Public, minimal `{ ok: true }`; do not expose model ids or secret configuration. |
| `GET /api/config` | Optional authenticated/safe model registry metadata for the UI. |
| `GET /api/me` | Authenticated profile + wallet summary. |
| `PATCH /api/me/profile` | Authenticated display name/avatar metadata update. |
| `GET /api/comics` | Authenticated list of current user's comics. |
| `POST /api/comics` | Authenticated create draft comic. |
| `GET /api/comics/:id` | Authenticated owner-only comic detail. |
| `PATCH /api/comics/:id` | Authenticated owner-only metadata/scenes update. |
| `POST /api/ai-text` | Authenticated or tightly rate-limited; persist useful text-generation metadata if it changes comic state. |
| `POST /api/generate-comic-page` | Authenticated, paid, idempotent, persists page and returns updated balance. |
| `GET /api/coin-packages` | Public or authenticated package list seeded from DB. |

Frontend changes should be scoped to a small API client wrapper in `scripts/creator.js` or a new `scripts/api.js`. Replace hardcoded demo credits/profile with `GET /api/me`, and replace local-only comic history with `/api/comics`.

## Deployment Approach

Recommended first production deployment:

- Vercel for static frontend + Express API.
- Neon Postgres for managed Postgres.
- Cloudflare R2 for generated images and uploaded avatars.
- Environment variables managed in the deployment platform, not `.env`.
- `vercel.json` with function duration and routing.
- `api/index.js` as the Vercel Express entrypoint.
- Root `server.js` remains for local `npm start`.

Why Vercel is acceptable now:

- Official docs document Express deployment.
- Fluid Compute defaults allow multi-minute Node functions, which fits synchronous OpenRouter generation better than older short serverless limits.
- Preview deployments help OAuth callback and environment validation.

Risk:

- If generation becomes background-worker-based, Vercel alone is not enough. The roadmap should keep the backend modular so `generation_jobs` can later move to a worker on Fly.io, Render, Railway, or another long-running compute host without rewriting the frontend.

## Environment Variables

Required:

```text
NODE_ENV
PORT
APP_URL
DATABASE_URL
SESSION_SECRET
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
YANDEX_CLIENT_ID
YANDEX_CLIENT_SECRET
OPENROUTER_API_KEY
OPENROUTER_SITE_URL
OPENROUTER_APP_NAME
OPENROUTER_TEXT_MODEL
OPENROUTER_IMAGE_MODEL
OPENROUTER_IMAGE_ASPECT_RATIO
STARTER_COINS
GENERATION_FULL_PAGE_COST
GENERATION_SCENE_COST
S3_ENDPOINT
S3_REGION
S3_BUCKET
S3_ACCESS_KEY_ID
S3_SECRET_ACCESS_KEY
S3_PUBLIC_BASE_URL
```

Keep `.env.example` updated and validate env at startup in `backend/src/config.js`. Fail fast when production-required variables are missing.

## Package Additions

Recommended install set:

```bash
npm install express express-session connect-pg-simple pg drizzle-orm arctic zod helmet express-rate-limit @aws-sdk/client-s3
npm install -D drizzle-kit vitest supertest
```

Add a lockfile immediately when dependencies are introduced.

Recommended scripts:

```json
{
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

## Phase Implications

1. **Backend foundation and safe static serving**
   - Add Express app structure.
   - Move or allowlist static assets.
   - Preserve `/api/health`, `/api/ai-text`, and `/api/generate-comic-page`.
   - Add normalized errors, request ids, timeouts, and tests for static path denial.

2. **Database and migrations**
   - Add Postgres, Drizzle schema, migrations, and seed packages.
   - Create users/profiles/wallets/ledger/comics/pages/payments tables before auth UI changes.
   - Add test database setup.

3. **OAuth and sessions**
   - Implement Google and Yandex login/callback/logout with Arctic.
   - Create user/profile/wallet on first login.
   - Grant starter coins through `coin_transactions`, not by directly setting a hidden balance.
   - Replace demo profile in `create.html`/`scripts/creator.js` with `/api/me`.

4. **Wallet ledger and paid generation**
   - Make `POST /api/generate-comic-page` require auth.
   - Add idempotency keys, wallet reservation/debit/refund, and insufficient-balance errors.
   - Return updated wallet state from successful generation.
   - Keep OpenRouter request construction in `backend/src/services/openrouter.js`.

5. **Comic history persistence**
   - Persist comic drafts, scenes, pages, prompt metadata, selected model, style, tone, status, and generated image object keys.
   - Add list/detail APIs and update `scripts/creator.js` to reopen user-owned comics.

6. **Object storage and profile avatars**
   - Store generated base64 images in R2/S3-compatible storage.
   - Add avatar upload limits, content-type validation, and old-object cleanup.

7. **Deployment and operational hardening**
   - Add `api/index.js`, `vercel.json`, deployment README, env documentation, and production smoke tests.
   - Add rate limits, CSRF protection for session-cookie writes, CSP/security headers, and structured error logging.

## Anti-Recommendations

Do not migrate the frontend to Next.js or React for this milestone. It would spend roadmap budget on UI plumbing while the real risk is backend correctness.

Do not keep expanding root `server.js`. It is already the wrong boundary for auth, persistence, and billing.

Do not store generated base64 images in Postgres. Store image objects in R2/S3 and only keep metadata/object keys in DB.

Do not trust any client-sent balance, cost, user id, provider id, or comic owner id. Every one of those must be derived from the session and database.

Do not run `express-session` MemoryStore in production. Use Postgres-backed sessions from the start.

Do not make OpenRouter calls from the browser. The existing same-origin server proxy is the correct security boundary; it just needs auth, rate limits, idempotency, and persistence.

## Confidence and Sources

| Claim | Confidence | Sources |
|-------|------------|---------|
| Express is deployable on Vercel and fits the brownfield app | HIGH | Vercel Express guide; Express 5 migration docs. |
| Server-side sessions should not use MemoryStore in production | HIGH | Express session docs. |
| Arctic supports Google/Yandex OAuth authorization-code clients | HIGH | Arctic v3 docs and provider docs. |
| PostgreSQL/Drizzle fits transactional ledger work | HIGH | Drizzle transaction docs; node-postgres pooling docs. |
| R2/S3-compatible storage is suitable for generated images | HIGH | Cloudflare R2 S3 compatibility docs; OpenRouter image docs note base64 image data. |
| Vercel is sufficient for first synchronous generation deployment | MEDIUM | Vercel Fluid Compute duration docs; actual generation latency and plan limits still need production validation. |

Sources:

- Express 5 migration: https://expressjs.com/en/guide/migrating-5.html
- Express session middleware: https://expressjs.com/en/resources/middleware/session.html
- Vercel Express guide: https://examples.vercel.com/guides/using-express-with-vercel
- Vercel function duration/limits: https://vercel.com/docs/functions/configuring-functions/duration
- Arctic v3 docs: https://arcticjs.dev/
- Arctic Yandex provider: https://arcticjs.dev/providers/yandex
- Google OAuth web server apps: https://developers.google.com/identity/protocols/oauth2/web-server
- Yandex ID OAuth/user info: https://yandex.com/dev/id/doc/en/concepts/ya-oauth-intro and https://yandex.com/dev/id/doc/en/user-information
- Drizzle transactions: https://orm.drizzle.team/docs/transactions
- Drizzle Neon/serverless Postgres notes: https://orm.drizzle.team/docs/connect-neon
- node-postgres pooling: https://node-postgres.com/features/pooling
- Cloudflare R2 S3 compatibility: https://developers.cloudflare.com/r2/api/s3/api/
- OpenRouter image generation: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
- OpenRouter API headers: https://openrouter.ai/docs/api-reference/overview
