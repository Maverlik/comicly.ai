# Phase 3 Research: OAuth Sessions And Profile Bootstrap

**Date:** 2026-04-27
**Mode:** lightweight
**Status:** complete

## Inputs

- `.planning/phases/03-oauth-sessions-and-profile-bootstrap/03-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `backend/BACKEND_TZ.md`
- Phase 2 summaries and verification
- Current backend files under `backend/app/`

## External Docs Checked

- Authlib FastAPI/Starlette OAuth client docs: `https://docs.authlib.org/en/stable/client/fastapi.html` and `https://docs.authlib.org/en/stable/client/starlette.html`
- Google OpenID Connect docs: `https://developers.google.com/identity/openid-connect/openid-connect`
- Yandex ID OAuth user information docs: `https://yandex.com/dev/id/doc/en/user-information`

## Findings

### OAuth Client Approach

Authlib is the best fit for the current FastAPI/Starlette backend because it supports async authorization redirect and callback token exchange through the Starlette request object. It expects temporary request session support for OAuth `state` handling, so Phase 3 should add Starlette `SessionMiddleware` for OAuth flow state only.

Important distinction for downstream implementation:

- Temporary OAuth state session: signed client-side middleware storage used to complete provider redirects.
- Product session: opaque random token stored in an `HttpOnly` cookie, hashed in `user_sessions`, and validated against the database.

The product session must not be replaced by Authlib's temporary middleware session.

### Provider Identity Shape

Google OpenID Connect userinfo includes stable subject identifiers and `email_verified`. Yandex ID exposes user information via `GET https://login.yandex.ru/info` using the OAuth token, with email available when the Email permission is requested.

Planning implication:

- Normalize provider profiles into a local DTO: provider, provider_user_id, email, email_verified, display_name, avatar_url.
- Google should require verified email for email-linking.
- Yandex should be treated as verified-email linkable only when docs/API response provides a reliable email verification signal or the implementation clearly documents why the returned email is trusted. If not available, Yandex should still login by provider id but skip cross-provider email merge.

### Session And Cookie Safety

The current Phase 2 schema already has `user_sessions.session_token_hash`, `expires_at`, and `revoked_at`. No schema migration is required for Phase 3 if the implementation stores a cryptographic hash of a random token and uses `expires_at` plus `revoked_at` checks.

Planning implication:

- Add session token generation/hash helpers.
- Store only token hash in DB.
- Set cookie with 30-day max age, `HttpOnly`, `Secure` in production, and `SameSite=Lax`.
- Make cookie domain configurable and allow `.comicly.ai` for production.

### First Login Bootstrap

Phase 2 already has enough schema for first-login bootstrap:

- `users`
- `provider_identities`
- `user_profiles`
- `wallets`
- `wallet_transactions`

Planning implication:

- Bootstrap should be transaction-scoped.
- Provider identity lookup by `(provider, provider_user_id)` is first.
- Verified-email account linking is second.
- Starter grant should use a stable idempotency key such as `starter-grant:{user_id}`.
- Phase 3 should create only the initial wallet and starter ledger entry. Generic credit/debit services stay Phase 4.

### Protected APIs

Phase 3 needs auth dependency plumbing before broader private APIs:

- Read session cookie.
- Hash token.
- Load non-revoked, non-expired session.
- Load user.
- Raise stable `ApiError` with an auth code when invalid/anonymous.

Planning implication:

- Add `get_current_user` or equivalent dependency.
- Add `GET /api/v1/me` for account/profile/wallet summary.
- Add display name update endpoint.
- Add logout endpoint that revokes current session and clears cookie.

## Recommended Plan Shape

1. Auth config, dependencies, cookie/session primitives, temporary OAuth state middleware.
2. Provider clients and OAuth redirect/callback routes with mocked provider tests.
3. First-login bootstrap service with provider identity linking, starter wallet, and idempotent ledger grant.
4. Protected `/me`, display-name update, logout, docs, and full quality gates.

## Risks And Mitigations

| Risk | Mitigation |
|------|------------|
| Confusing Authlib temporary session with product session | Name and document them separately; product session stays DB-backed. |
| Duplicate starter grants on callback retry | Stable `wallet_transactions.idempotency_key` and transaction-scoped bootstrap. |
| Incorrect account merge by unverified email | Only link by verified email; otherwise provider-id login only. |
| Cross-site cookie misconfiguration | Configurable cookie domain/secure/samesite plus tests for production/local settings. |
| Live OAuth tests are flaky and secret-dependent | Use mocked provider client/profile fixtures in automated tests. |

## RESEARCH COMPLETE
