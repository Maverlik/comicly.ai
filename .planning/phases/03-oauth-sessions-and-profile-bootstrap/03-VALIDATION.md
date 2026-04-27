# Phase 3 Validation Strategy

**Phase:** 03-oauth-sessions-and-profile-bootstrap
**Status:** ready

## Requirement Coverage

| Requirement | Planned Coverage |
|-------------|------------------|
| AUTH-01 | Google OAuth login route, callback handling, server-side session cookie tests. |
| AUTH-02 | Yandex OAuth login route, callback handling, server-side session cookie tests. |
| AUTH-03 | First-login bootstrap creates user, provider identity, profile, wallet, and starter ledger entry. |
| AUTH-04 | Returning OAuth login attaches by provider id; second provider links by verified email. |
| AUTH-05 | Logout revokes current session and clears cookie. |
| AUTH-06 | Auth dependency rejects anonymous/invalid sessions; private APIs use it. |
| AUTH-07 | Cookie flag/config tests cover `HttpOnly`, production `Secure`, and `SameSite=Lax`. |
| PROF-01 | `GET /api/v1/me` returns account/profile/wallet summary from DB. |
| PROF-02 | Authenticated display-name update persists and appears in `/me`. |
| TEST-02 | OAuth/session behavior covered with mocked provider fixtures. |

## Gates

Run from `backend/`:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Use fail-fast chaining for final plan verification:

```powershell
python -m pytest && python -m ruff check . && python -m ruff format --check .
```

## Phase-Level Acceptance

- No frontend/root runtime files changed.
- OAuth provider credentials are loaded from env and never exposed in responses.
- Login redirects are backend-owned and redirect to configurable creator URL after success.
- Product sessions are opaque, DB-backed, hashed at rest, expiring after 30 days by default.
- Authenticated bootstrap and profile update endpoints use stable error envelope.
- Avatar upload is not implemented; OAuth avatar URL only.

## Known Non-Goals

- Wallet debits, insufficient balance checks, and concurrent wallet operations.
- Comic persistence APIs.
- OpenRouter generation migration.
- Real avatar upload/storage.
- Frontend login integration.
