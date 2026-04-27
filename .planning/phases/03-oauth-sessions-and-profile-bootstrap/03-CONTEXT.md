# Phase 3: OAuth Sessions And Profile Bootstrap - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers backend API-only OAuth login and server-side session bootstrap for Google and Yandex. It creates or links users, provider identities, profiles, wallets, and the starter coin ledger entry on first login; exposes trusted account/profile/wallet bootstrap data; supports display-name updates; and supports logout/session revocation.

This phase does not integrate the frontend, does not implement wallet debit/generation logic, does not implement comic persistence, does not implement payments, and does not upload avatar files to object storage.

</domain>

<decisions>
## Implementation Decisions

### OAuth Flow

- **D-01:** Use backend-owned OAuth redirect flow for both providers.
- **D-02:** Login routes should be under `/api/v1/auth/...`, for example `GET /api/v1/auth/google/login` and `GET /api/v1/auth/yandex/login`.
- **D-03:** Provider callbacks are handled by the backend. The backend validates authorization codes/tokens server-side and never trusts browser-supplied identity claims.
- **D-04:** After successful login, redirect the browser to `https://comicly.ai/create.html` for production MVP.
- **D-05:** Redirect target should be configurable through env so local/dev can use the matching local creator URL without code changes.

### Account Linking

- **D-06:** Link Google and Yandex provider identities to the same existing account when the provider returns the same verified email.
- **D-07:** If email is missing or not provider-verified, fall back to provider-specific identity matching only and do not silently merge accounts.
- **D-08:** Returning users attach by `(provider, provider_user_id)` first; verified-email linking is a secondary path for adding a new provider to an existing user.

### Sessions And Cookies

- **D-09:** Use server-side DB sessions, not stateless JWT sessions.
- **D-10:** The browser cookie stores only an opaque random session token. The database stores only a hash of that token in `user_sessions.session_token_hash`.
- **D-11:** Session lifetime is 30 days for MVP.
- **D-12:** Logout revokes the current server-side session by setting `revoked_at`.
- **D-13:** Production cookies should be `HttpOnly`, `Secure`, and `SameSite=Lax`.
- **D-14:** Production cookie domain should support the frontend/backend split: frontend `comicly.ai`/`www.comicly.ai`, backend `api.comicly.ai`. Prefer `.comicly.ai` if implementation/testing confirms it works with the deployment shape.
- **D-15:** CORS/credentials must allow only configured frontend origins, not wildcard origins.

### First Login Bootstrap

- **D-16:** First successful OAuth login creates `users`, `provider_identities`, `user_profiles`, `wallets`, and one starter coin `wallet_transactions` row.
- **D-17:** Starter coin amount comes from runtime settings (`STARTER_COINS`), currently defaulting to 100.
- **D-18:** The initial starter grant must be idempotent so retries or repeated callback processing do not double-grant coins.
- **D-19:** Full wallet ledger/debit business logic remains Phase 4; Phase 3 only creates the initial wallet and starter grant needed for bootstrap.

### Account/Profile APIs

- **D-20:** Backend remains API-only in Phase 3. Do not edit frontend/root files.
- **D-21:** Add an authenticated bootstrap endpoint such as `GET /api/v1/me` returning account, profile, and wallet summary from the database.
- **D-22:** Add display-name update through authenticated backend API.
- **D-23:** Use provider avatar URL from OAuth as the initial `avatar_url` when available.
- **D-24:** Do not implement avatar file upload in Phase 3. Real avatar upload is deferred until object storage is selected (for example Vercel Blob, S3, or Cloudflare R2).

### Error And Test Shape

- **D-25:** Private APIs must reject anonymous requests with the existing stable error envelope and a machine-readable auth error code.
- **D-26:** OAuth provider behavior should be tested with mocked provider callbacks/fixtures, not live external OAuth in automated tests.
- **D-27:** Tests should cover first login, returning provider login, verified-email provider linking, logout/revocation, anonymous rejection, cookie flags/config behavior, and `/api/v1/me` bootstrap shape.

### the agent's Discretion

- Exact OAuth helper library choice, provided it works with FastAPI, Google OAuth, Yandex OAuth, async SQLAlchemy, and test fixtures.
- Exact endpoint names under `/api/v1/auth/...`, as long as they are clear and stable.
- Exact internal service/module decomposition, following existing backend patterns.
- Exact local redirect URL default, as long as production redirect to `https://comicly.ai/create.html` is configurable and documented.

</decisions>

<specifics>
## Specific Ideas

- User wants login to land directly in the creator experience for MVP, not on a marketing page.
- User prefers one human account across Google/Yandex when the verified email matches.
- User wants Phase 3 to avoid premature storage decisions; OAuth avatar URL is enough for now.
- User explicitly wants backend API-only work in this phase.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Phase Scope And Requirements

- `.planning/ROADMAP.md` - Phase 3 goal, success criteria, and dependency on Phase 2.
- `.planning/REQUIREMENTS.md` - AUTH-01 through AUTH-07, PROF-01, PROF-02, and TEST-02 requirements.
- `.planning/PROJECT.md` - Product principles, backend/auth context, and out-of-scope items.
- `.planning/STATE.md` - Current milestone state and prior decisions.
- `backend/BACKEND_TZ.md` - Backend source-of-truth requirements from the user.

### Prior Phase Outputs

- `.planning/phases/02-data-and-payment-foundation/02-VERIFICATION.md` - Confirms the schema, wallet, payment, seed, and catalog foundation available to Phase 3.
- `.planning/phases/02-data-and-payment-foundation/02-01-SUMMARY.md` - Model/config/session foundations created in Phase 2.
- `.planning/phases/02-data-and-payment-foundation/02-02-SUMMARY.md` - Initial Alembic schema and constraints.
- `.planning/phases/02-data-and-payment-foundation/02-03-SUMMARY.md` - Coin package seed/catalog and docs.

### Backend Code To Inspect

- `backend/app/core/config.py` - Settings pattern, env behavior, starter coin config.
- `backend/app/db/session.py` - Async DB session dependency pattern.
- `backend/app/models/user.py` - User, provider identity, profile, and session models.
- `backend/app/models/wallet.py` - Wallet and transaction models used for first-login bootstrap.
- `backend/app/main.py` - App/router/error handler setup.
- `backend/app/api/v1/coin_packages.py` - Existing `/api/v1` route style and dependency injection pattern.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `Settings` already supports env-driven config and `starter_coins`.
- `get_async_session` already exists as a FastAPI dependency for DB-backed routes.
- `User`, `ProviderIdentity`, `UserProfile`, `UserSession`, `Wallet`, and `WalletTransaction` tables already exist.
- Existing error envelope is implemented through `ApiError` and `error_response`.

### Established Patterns

- Backend is standalone FastAPI under `backend/`.
- Business APIs use `/api/v1/...`.
- Tests use pytest/httpx ASGI clients and async SQLAlchemy fixtures where useful.
- Alembic owns schema creation; runtime code should not call `create_all()` outside tests.

### Integration Points

- New auth routers should be included from `backend/app/main.py` through the `/api/v1` router surface.
- Auth-required route dependencies should integrate with the existing stable error envelope.
- First-login bootstrap should write user/profile/wallet/session data inside backend service functions, leaving Phase 4 wallet operations for later.

</code_context>

<deferred>
## Deferred Ideas

- Avatar file upload and object storage cleanup are deferred until storage provider selection.
- Frontend login button/callback handling is deferred to Phase 7 unless separately approved.
- Wallet debit, insufficient balance, idempotent generation charging, and concurrency-safe wallet operations are Phase 4.
- Comic draft/page persistence is Phase 5.
- OpenRouter generation and durable generated image handling are Phase 6.

</deferred>

---

*Phase: 03-oauth-sessions-and-profile-bootstrap*
*Context gathered: 2026-04-27*
