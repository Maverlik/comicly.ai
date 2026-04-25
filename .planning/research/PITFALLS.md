# Domain Pitfalls

**Domain:** Comicly.ai production backend
**Researched:** 2026-04-25
**Scope:** Production auth, credits, persistence, OpenRouter generation, and deployment
**Overall confidence:** HIGH for project-specific risks from local code and planning docs; MEDIUM for operational risks that depend on the final host, database, and object storage choices.

## Roadmap Phase Labels Used

No roadmap phase file exists yet, so this research maps risks to recommended backend phases:

| Phase | Name | Primary Goal |
|-------|------|--------------|
| Phase 1 | Backend Foundation and Safety | Split `server.js`, add config validation, static file allowlist, tests, and baseline API structure. |
| Phase 2 | Auth and Sessions | Add Google/Yandex OAuth, server sessions, logout, CSRF/session cookie policy, and private route guards. |
| Phase 3 | Persistence Model | Add database migrations for users, identities, profiles, wallets, comics, pages, generation jobs, payments, and packages. |
| Phase 4 | Wallet and Credits | Make wallet balance authoritative, add transaction ledger, idempotency, insufficient-balance errors, and refund rules. |
| Phase 5 | OpenRouter Generation Pipeline | Protect generation routes, persist jobs/pages, handle timeouts/retries/provider errors, and store generated image assets. |
| Phase 6 | Frontend Backend Integration | Replace demo profile, client credits, and volatile comic state with authenticated API data while preserving creator UX. |
| Phase 7 | Payment-Ready Data | Seed coin packages and payment tables without integrating a real acquiring provider yet. |
| Phase 8 | Deployment and Operations | Add production configuration, env docs, runtime pinning, deployment instructions, logging, health checks, and smoke tests. |

## Critical Pitfalls

### Pitfall 1: Serving the Repository Root in Production
**What goes wrong:** The current static route can serve any regular file under the repo root, including `.env`, `.planning/`, backend specs, package metadata, or future migration files.
**Why it happens:** `server.js` resolves requests against `__dirname` and only checks a string prefix before streaming the file.
**Warning signs:** Production preview exposes `/.env`, `/backend/BACKEND_TZ.md`, `/.planning/PROJECT.md`, `/package.json`, or other non-public paths; static server tests only cover happy-path HTML/CSS/JS.
**Prevention strategy:** In Phase 1, serve only an explicit public directory or explicit asset map. Deny dotfiles, planning docs, backend docs, config files, package metadata, unknown extensions, and encoded traversal attempts. Use `path.resolve()` with a path-segment containment check. Add tests for `/.env`, `.planning`, `backend`, traversal, encoded traversal, and `HEAD`.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety.

### Pitfall 2: Adding Auth Around an Unsafe Monolith Instead of Creating Boundaries First
**What goes wrong:** Auth, billing, routing, OpenRouter calls, and static serving remain tangled in `server.js`, making every backend change risky and hard to test.
**Why it happens:** The current server mixes env loading, prompt construction, provider calls, JSON parsing, health checks, static serving, and route dispatch in one file.
**Warning signs:** New OAuth or wallet code is added directly into the existing route branches; tests require starting the whole server for every helper; route handlers mutate shared globals or read env directly.
**Prevention strategy:** In Phase 1, create small modules for config, HTTP routing, auth middleware, static serving, OpenRouter client, validation, persistence adapters, and feature handlers. Preserve existing API response contracts while moving behavior behind testable functions.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety.

### Pitfall 3: Trusting Browser Credits or Browser Identity During Migration
**What goes wrong:** Users can spend beyond their balance, fake credits, call generation directly, or operate as another user if server APIs accept client-owned balance or identity fields.
**Why it happens:** `scripts/creator.js` currently starts with `credits = 240`, decrements locally after success, includes an `addCredits()` helper, and sends generation requests without auth or balance checks.
**Warning signs:** API payloads include `userId`, `balance`, `credits`, or `price` from the browser; frontend still decrements credits optimistically; direct `curl` requests can generate images without a session and wallet row.
**Prevention strategy:** In Phase 4, make the database wallet and transaction ledger the only source of truth. The browser may display balances returned by backend APIs, but all reads, debits, credits, refunds, and insufficient-balance decisions must happen server-side.
**Roadmap phase:** Phase 4 - Wallet and Credits, with frontend removal completed in Phase 6.

### Pitfall 4: Non-Atomic Coin Debit and Page Persistence
**What goes wrong:** Users lose coins when OpenRouter fails, get free generated pages when persistence fails, or see wallet balances that disagree with transaction history.
**Why it happens:** Generation is a multi-step workflow: validate session, check balance, call provider, store result, update page/job status, debit wallet, and return updated state. Partial failures can leave inconsistent state.
**Warning signs:** Wallet balance is updated separately from transaction log; generated pages can exist without a matching debit; failed jobs debit coins without automatic refund; ledger sum does not equal wallet balance.
**Prevention strategy:** In Phase 4 and Phase 5, define one authoritative generation state machine. Prefer reserving coins in a transaction before provider execution, then commit debit on success or release/refund on failure. Persist job status and transaction references. Add reconciliation tests that wallet balance equals ledger sum.
**Roadmap phase:** Phase 4 - Wallet and Credits, enforced in Phase 5 - OpenRouter Generation Pipeline.

### Pitfall 5: Missing Idempotency for Double Clicks, Retries, and Network Replays
**What goes wrong:** A double click, browser retry, mobile reconnect, or reverse-proxy retry creates multiple OpenRouter calls and multiple debits for one user intent.
**Why it happens:** Current generation calls are synchronous HTTP requests with no idempotency key or generation job identity.
**Warning signs:** Logs show duplicate generation requests with identical payloads within seconds; the UI disables a button but API calls still duplicate under direct requests; same page gets multiple debit transactions.
**Prevention strategy:** In Phase 4, require an idempotency key for billable generation. Store idempotency key scoped to user and operation. Return the existing job/result for duplicates. Add a unique constraint and tests for concurrent duplicate requests.
**Roadmap phase:** Phase 4 - Wallet and Credits.

### Pitfall 6: Using OAuth Provider Email as the Primary Account Key
**What goes wrong:** Separate provider accounts collide, verified/unverified emails are misused, or a changed email disconnects the user from their account.
**Why it happens:** The backend spec requires Google and Yandex login, and provider data includes email/name/avatar, but account linking must be based on provider and provider user id.
**Warning signs:** `users.email` is the only lookup for login; new identities overwrite existing users by email; code accepts user identifiers from the browser after OAuth; unverified email creates account ownership decisions.
**Prevention strategy:** In Phase 2 and Phase 3, create `provider_identities` with `(provider, provider_user_id)` unique. Use email only for profile display and optional secondary matching after explicit policy. Validate authorization code/token server-side only.
**Roadmap phase:** Phase 2 - Auth and Sessions, schema support in Phase 3 - Persistence Model.

### Pitfall 7: Session Cookies That Work Locally but Fail or Leak in Production
**What goes wrong:** Users cannot stay logged in on production, CSRF protection is absent, cookies are sent over insecure channels, or auth breaks across domains.
**Why it happens:** Production OAuth requires exact redirect URIs, secure cookies, correct `SameSite`, proxy-aware HTTPS detection, and consistent `APP_URL` behavior.
**Warning signs:** Login works on localhost but loops on production; cookies lack `HttpOnly`, `Secure`, or `SameSite`; API routes use permissive CORS with credentials; logout only changes frontend state.
**Prevention strategy:** In Phase 2, implement server-managed sessions with `HttpOnly`, `Secure` in production, `SameSite=Lax` or stricter, session rotation on login, logout invalidation, CSRF strategy for state-changing form/API requests, and explicit allowed origins.
**Roadmap phase:** Phase 2 - Auth and Sessions, production verification in Phase 8.

### Pitfall 8: Private Comic Data Without Ownership Checks
**What goes wrong:** A logged-in user can fetch, update, or regenerate pages for another user's comic by guessing IDs.
**Why it happens:** Persistence introduces `comics`, `pages`, and generation jobs, but access control can be missed if route handlers query by id only.
**Warning signs:** SQL queries use `WHERE id = ?` without `user_id`; tests create only one user; frontend URLs expose plain numeric comic IDs and API accepts them without session ownership filters.
**Prevention strategy:** In Phase 3 and Phase 6, every private query must scope by authenticated `user_id`. Add integration tests with two users for list, read, update, page creation, generation, archive, and profile routes.
**Roadmap phase:** Phase 3 - Persistence Model, enforced in Phase 6 - Frontend Backend Integration.

### Pitfall 9: Depending on OpenRouter-Hosted Image URLs as Permanent Assets
**What goes wrong:** Saved comics later show broken images, expired URLs, provider CDN restrictions, or mixed privacy behavior.
**Why it happens:** The current backend returns `imageUrl` directly from OpenRouter and the frontend stores it in memory. The production requirement is durable comic history.
**Warning signs:** Database stores only provider URLs or data URLs; there is no object storage key; reopening a comic depends on the original provider URL; generated image URLs are not validated before storage.
**Prevention strategy:** In Phase 5, copy successful generated images into project-owned object storage and store storage keys plus metadata. Validate URL scheme and content type. Keep provider response metadata for audit but do not rely on provider-hosted URLs for history.
**Roadmap phase:** Phase 5 - OpenRouter Generation Pipeline.

### Pitfall 10: Synchronous Long-Running Generation as the Only Production Flow
**What goes wrong:** Requests hang, users retry and duplicate spending, serverless functions time out, and the UI cannot recover from provider stalls.
**Why it happens:** Current server and frontend use direct `fetch()` calls with no timeout, abort, job queue, polling endpoint, or persisted status.
**Warning signs:** Generation requests remain open until proxy/serverless timeout; browser loading state never resolves; provider stalls produce no job record; errors are visible only as generic toasts.
**Prevention strategy:** In Phase 5, introduce generation jobs with persisted statuses: `queued`, `running`, `succeeded`, `failed`, `refunded` or equivalent. Add server-side timeouts with `AbortController`, retry policy only for safe cases, polling or resume endpoint, and clear frontend states.
**Roadmap phase:** Phase 5 - OpenRouter Generation Pipeline.

### Pitfall 11: Rate Limiting After Launch Instead of Before AI Exposure
**What goes wrong:** Anonymous or scripted traffic consumes OpenRouter credits, overloads the Node process, or brute-forces auth callbacks.
**Why it happens:** Current `/api/ai-text` and `/api/generate-comic-page` endpoints are unauthenticated and unlimited.
**Warning signs:** `/api/ai-text` remains public after auth lands; no per-user or per-IP counters; generation route checks balance but allows unlimited failed attempts; logs show high repeated requests from one IP/session.
**Prevention strategy:** In Phase 2 and Phase 5, protect AI endpoints with sessions, per-user limits, per-IP limits for unauthenticated auth paths, body-size limits, request validation, and queue depth controls. Return stable error codes for rate-limited states.
**Roadmap phase:** Phase 2 - Auth and Sessions for route protection; Phase 5 - OpenRouter Generation Pipeline for generation limits.

### Pitfall 12: No Automated Tests for Billing, Auth, and Static Safety
**What goes wrong:** Security and wallet regressions ship undetected because manual smoke checks miss edge cases and concurrency.
**Why it happens:** `package.json` has no test runner, no test files, and no test scripts. The current app is structured as runtime files, not testable modules.
**Warning signs:** Backend phases add dependencies and schema without `npm test`; reviewers validate credits by clicking UI only; no tests for insufficient balance, duplicate idempotency keys, static deny paths, or two-user authorization.
**Prevention strategy:** In Phase 1, add a minimal Node-compatible test runner and module boundaries. Required early tests: static denylist, JSON validation, auth guard, session cookie flags, wallet debit/refund, ledger reconciliation, idempotency, OpenRouter fixtures, and cross-user access denial.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety, expanded in every later phase.

## Moderate Pitfalls

### Pitfall 13: Model Registry Drift Between Frontend and Backend
**What goes wrong:** The UI offers models the backend rejects, the backend default is not visible in the UI, pricing labels drift from actual costs, or provider capability assumptions become wrong.
**Warning signs:** `create.html`, `scripts/creator.js`, and `server.js` each contain separate model IDs; pricing text is hardcoded outside the backend; default model is not in `ALLOWED_IMAGE_MODELS`.
**Prevention strategy:** In Phase 1 or Phase 5, create a backend model registry with safe public metadata. Expose allowed model IDs, labels, capabilities, and coin cost through a config API. Keep provider IDs and cost rules server-side authoritative.
**Roadmap phase:** Phase 5 - OpenRouter Generation Pipeline.

### Pitfall 14: Prompt and Payload Growth Without Validation
**What goes wrong:** Users send oversized or malformed scene data, provider cost and latency spike, generated content becomes unstable, or logs store excessive personal text.
**Warning signs:** Only `story` is validated; arrays and fields are concatenated directly into prompts; request body size is the only meaningful limit; prompt templates are changed without fixtures.
**Prevention strategy:** In Phase 1 and Phase 5, validate every field with length limits, allowed enum values, array bounds, and text normalization. Version prompt templates and store prompt version with generation jobs, not necessarily full raw prompt unless retention policy allows it.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety, completed in Phase 5.

### Pitfall 15: HTML or URL Injection Through Persisted Generated Assets
**What goes wrong:** A stored `imageUrl` or avatar URL injects unsafe markup, loads unsupported schemes, or creates XSS when rendered into `innerHTML`.
**Warning signs:** Persisted image URLs are inserted into HTML template strings; avatar upload returns arbitrary URL; image URL scheme is not restricted to `https:` or owned object storage; frontend keeps using `button.innerHTML` for external values.
**Prevention strategy:** In Phase 6, render persisted URLs with DOM property assignment, validate URL schemes on the backend, store only owned object-storage keys where possible, and add CSP/security headers in Phase 1/8.
**Roadmap phase:** Phase 6 - Frontend Backend Integration, with static/header support in Phase 1 and Phase 8.

### Pitfall 16: Avatar Upload Becoming an Unbounded File Storage Problem
**What goes wrong:** Users upload huge files, unsupported formats, executable content, or orphaned avatars that accumulate storage cost.
**Warning signs:** Upload route accepts arbitrary MIME types; file size limit is absent or only client-side; old avatars are never marked for cleanup; returned avatar URLs bypass object storage controls.
**Prevention strategy:** In Phase 3 and Phase 6, store avatar metadata separately, enforce server-side content type and size limits, generate storage keys per user, and either delete or garbage-collect superseded avatars.
**Roadmap phase:** Phase 6 - Frontend Backend Integration, schema/storage support in Phase 3.

### Pitfall 17: Health Endpoint Leaking Operational Configuration
**What goes wrong:** Public users can infer API key configuration, active model IDs, or deployment mistakes.
**Warning signs:** Production `/api/health` returns `hasApiKey`, `imageModel`, or `textModel`; frontend depends on public diagnostics for normal UX; health check output differs by secret presence.
**Prevention strategy:** In Phase 1, make public health minimal, for example `{ "ok": true }`. Move detailed configuration diagnostics to authenticated admin/debug tooling or local-only logs.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety.

### Pitfall 18: Payment Tables Designed Too Narrowly for Future Provider Webhooks
**What goes wrong:** Later payment integration requires schema rewrites because payments cannot represent provider IDs, status transitions, external event IDs, currency, amount, package snapshots, idempotency, or failed/canceled states.
**Warning signs:** Payment table only has `user_id`, `coins`, and `paid`; package price is not snapshotted; no unique external provider payment/event fields; coin crediting cannot be linked to payment events.
**Prevention strategy:** In Phase 7, prepare provider-agnostic `coin_packages` and `payments` with immutable package snapshots, status history or timestamps, provider fields, external IDs, and room for webhook idempotency. Do not grant coins from fake payment states in this milestone.
**Roadmap phase:** Phase 7 - Payment-Ready Data.

### Pitfall 19: Environment Configuration That Is Optional Until Runtime Failure
**What goes wrong:** Production starts with missing OAuth secrets, weak session secret, wrong `APP_URL`, wrong OpenRouter referer, missing database URL, or local-only defaults.
**Warning signs:** App boots with empty `SESSION_SECRET`; env validation happens only when a route is called; OAuth redirect URI mismatch appears only after deployment; docs do not list required env vars.
**Prevention strategy:** In Phase 1 and Phase 8, validate required env at startup by environment mode. Provide `.env.example`, deployment env checklist, and fail-fast behavior for production-critical secrets.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety, production hardening in Phase 8.

### Pitfall 20: Deploying to a Runtime That Does Not Match Stateful Backend Assumptions
**What goes wrong:** Serverless timeouts, ephemeral filesystem, missing Node 22 APIs, or connection pooling limits break generation, sessions, uploads, or database access.
**Warning signs:** Deployment target is chosen before deciding whether generation is queued or synchronous; generated files are written to local disk; sessions are in process memory; Node runtime is below the required version.
**Prevention strategy:** In Phase 8, pin Node 22+, use database/object storage for durable state, avoid in-memory sessions, document whether the host is serverless or long-running Node, and run production smoke tests for OAuth, DB, generation, cookies, and static safety.
**Roadmap phase:** Phase 8 - Deployment and Operations.

## Minor Pitfalls

### Pitfall 21: Keeping Demo UI Actions After Backend Launch
**What goes wrong:** Users see fake notifications, fake logout, fake profile actions, or a hidden add-credits path that conflicts with real account state.
**Warning signs:** `addCredits()` still exists in production frontend; logout toast says demo profile; profile menu actions do not call backend APIs.
**Prevention strategy:** In Phase 6, remove or disable demo-only actions and replace them with authenticated API flows. Add browser smoke tests for profile, logout, and balance display.
**Roadmap phase:** Phase 6 - Frontend Backend Integration.

### Pitfall 22: Undo History Capturing Large or Trusted Server State
**What goes wrong:** Browser memory grows with generated images or undo restores stale balances/profile data that should come only from the server.
**Warning signs:** `history` snapshots include server balance, external image data URLs, or full page arrays after persistence lands; undo changes visible wallet balance.
**Prevention strategy:** In Phase 6, keep undo scoped to editable draft fields and local page selection. Store page IDs/storage keys instead of large image data, and never let undo mutate authoritative account or wallet state.
**Roadmap phase:** Phase 6 - Frontend Backend Integration.

### Pitfall 23: Poor Error Codes for Product-Critical States
**What goes wrong:** Frontend cannot distinguish insufficient balance, unauthenticated session, rate limit, provider failure, validation error, and retryable timeout.
**Warning signs:** Every backend failure returns `{ error }` with 500 or generic toast text; insufficient balance is not a stable code; provider errors leak raw messages.
**Prevention strategy:** In Phase 1 and Phase 4/5, define stable API error codes: `UNAUTHENTICATED`, `FORBIDDEN`, `INSUFFICIENT_COINS`, `RATE_LIMITED`, `VALIDATION_ERROR`, `GENERATION_TIMEOUT`, `PROVIDER_ERROR`, and `MISSING_CONFIG` for local diagnostics.
**Roadmap phase:** Phase 1 - Backend Foundation and Safety, expanded in Phase 4 and Phase 5.

### Pitfall 24: Replacing Existing AI Routes Abruptly
**What goes wrong:** Existing creator features break while backend auth/persistence is added, causing a production milestone to regress the demo experience.
**Warning signs:** `/api/ai-text` or `/api/generate-comic-page` response shape changes without a frontend migration; older frontend code expects `imageUrl` but backend returns only job ID; no compatibility tests.
**Prevention strategy:** In Phase 5 and Phase 6, either preserve current response shape until frontend migration is complete or version the routes. Add integration tests around the existing route contracts before changing them.
**Roadmap phase:** Phase 5 - OpenRouter Generation Pipeline and Phase 6 - Frontend Backend Integration.

## Phase-Specific Warning Matrix

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Phase 1 - Backend foundation | Static secret exposure; untestable monolith; weak env validation | Split modules, static allowlist, fail-fast config, and add tests before auth/wallet work. |
| Phase 2 - Auth/session | Provider identity collision; insecure cookies; login works locally only | Use `(provider, provider_user_id)`, server-side OAuth validation, secure cookie policy, and production redirect tests. |
| Phase 3 - Persistence | Cross-user access; schema too narrow for jobs/payments/assets | Include ownership columns, constraints, status fields, object-storage keys, and two-user authorization tests. |
| Phase 4 - Wallet/credits | Double debit, lost coins, inconsistent ledger | Use transactions, idempotency keys, reservation/refund rules, unique constraints, and reconciliation checks. |
| Phase 5 - OpenRouter generation | Hung requests, duplicate provider calls, broken image history | Use generation jobs, timeouts, provider fixtures, object storage copy, rate limits, and persisted status. |
| Phase 6 - Frontend integration | Demo state fights backend truth | Remove fake credits/profile/logout; hydrate state from APIs; keep undo limited to drafts. |
| Phase 7 - Payment prep | Future webhook rewrite | Store package snapshots, provider references, status transitions, and webhook idempotency fields now. |
| Phase 8 - Deployment | Runtime mismatch and missing secrets | Pin runtime, document env, avoid local disk/in-memory sessions, run production smoke tests. |

## Minimum Acceptance Tests to Prevent These Pitfalls

| Area | Required Tests |
|------|----------------|
| Static serving | Public files return 200; `.env`, `.planning`, `backend`, traversal, encoded traversal, and package metadata return 403/404; `HEAD` returns no body. |
| Auth | Google/Yandex callback validates server-side; session cookie flags are correct; logout invalidates session; private route rejects anonymous users. |
| Authorization | Two users cannot read, update, generate into, or list each other's comics/pages. |
| Wallet | Insufficient balance blocks generation; debit writes ledger row; ledger sum matches balance; failed generation releases/refunds coins. |
| Idempotency | Duplicate keys return one job/result and one debit under concurrent requests. |
| OpenRouter | Missing key, provider non-OK, malformed response, no image, timeout, and successful image response all map to stable API states. |
| Persistence | Generated page survives refresh/relogin and references owned object storage, not only provider URL. |
| Deployment | Production URL loads; OAuth works on production domain; DB is connected; secure cookies are set; health endpoint is minimal. |

## Sources

- `.planning/PROJECT.md` - production backend goals, active requirements, constraints, and key decisions.
- `.planning/codebase/CONCERNS.md` - existing backend, security, scaling, dependency, and test risks.
- `.planning/codebase/TESTING.md` - absence of test framework and recommended test targets.
- `backend/BACKEND_TZ.md` - backend requirements for OAuth, sessions, wallet, comic history, payments-ready schema, deployment, and acceptance criteria. The file appears mojibaked in the local shell output, but the relevant requirements are still recoverable from the text structure and project summary.
- `server.js` - current static server, health route, JSON parsing, OpenRouter proxy, model allowlist, and generation handlers.
- `scripts/creator.js` - current client-owned creator state, demo credits/profile behavior, generation calls, and UI history handling.
