---
phase: 03-oauth-sessions-and-profile-bootstrap
plan: 02
subsystem: auth
tags: [oauth, google, yandex, sqlalchemy]
requires:
  - phase: 03-01-auth-config-and-session-primitives
    provides: settings, cookie helpers, OAuth state middleware
provides:
  - Google/Yandex OAuth login and callback route surface
  - Provider profile normalization
  - First-login user/profile/wallet bootstrap
  - Verified-email provider linking
affects: [phase-03, phase-04, phase-07]
tech-stack:
  added: []
  patterns: [provider-service-boundary, verified-email-linking, starter-grant-idempotency]
key-files:
  created:
    - backend/app/api/v1/auth.py
    - backend/app/services/oauth_providers.py
    - backend/app/services/auth_bootstrap.py
    - backend/tests/test_oauth_routes.py
    - backend/tests/test_auth_bootstrap.py
  modified:
    - backend/app/api/v1/__init__.py
key-decisions:
  - "Provider identity lookup wins before verified-email linking."
  - "Unverified or missing provider email does not merge accounts."
patterns-established:
  - "Live OAuth calls stay behind service abstractions so route tests use fakes."
requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-04, TEST-02]
duration: 18 min
completed: 2026-04-27
---

# Phase 3 Plan 02: OAuth Routes And Bootstrap Summary

**Backend-owned Google/Yandex OAuth routes with fixture-tested account bootstrap and verified-email linking**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-27T14:12:00+03:00
- **Completed:** 2026-04-27T14:30:00+03:00
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `/api/v1/auth/google/login`, `/api/v1/auth/yandex/login`, and matching callback routes.
- Added normalized provider profile DTOs for Google and Yandex payloads.
- Added transaction-scoped bootstrap for user, provider identity, profile, wallet, and starter ledger transaction.
- Covered returning-provider login, verified-email linking, and unverified-email non-linking.

## Task Commits

Implementation is included in `64a1cd4` (`feat(03): implement oauth session profile APIs`).

## Files Created/Modified

- `backend/app/api/v1/auth.py` - Login/callback OAuth routes.
- `backend/app/services/oauth_providers.py` - Provider client boundary and normalization.
- `backend/app/services/auth_bootstrap.py` - First-login bootstrap and provider linking.
- `backend/tests/test_oauth_routes.py` - Mocked route and provider normalization coverage.
- `backend/tests/test_auth_bootstrap.py` - Bootstrap/linking tests.

## Decisions Made

- OAuth callback success redirects to `FRONTEND_CREATOR_URL`.
- OAuth provider failure redirects to the creator URL with a stable `auth_error=oauth_failed` query.
- Yandex email linking is allowed only when normalized profile data marks the email verified/trusted.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope creep.

## Issues Encountered

None.

## User Setup Required

None - provider dashboard callback URLs are documented in `backend/README.md`.

## Next Phase Readiness

Ready for current-user dependency, `/api/v1/me`, profile update, and logout.

---
*Phase: 03-oauth-sessions-and-profile-bootstrap*
*Completed: 2026-04-27*
