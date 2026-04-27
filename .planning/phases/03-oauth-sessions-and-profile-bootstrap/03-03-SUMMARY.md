---
phase: 03-oauth-sessions-and-profile-bootstrap
plan: 03
subsystem: api
tags: [fastapi, auth, profile, wallet]
requires:
  - phase: 03-02-oauth-routes-and-bootstrap
    provides: user/session bootstrap and provider identities
provides:
  - Current-user dependency from DB-backed session cookie
  - Authenticated `/api/v1/me`
  - Display-name update endpoint
  - Current-session logout
affects: [phase-04, phase-05, phase-07]
tech-stack:
  added: []
  patterns: [current-user-dependency, authenticated-bootstrap-response]
key-files:
  created:
    - backend/app/api/v1/me.py
    - backend/app/services/current_user.py
    - backend/app/services/profiles.py
    - backend/tests/test_current_user.py
    - backend/tests/test_me_api.py
  modified:
    - backend/app/api/v1/__init__.py
key-decisions:
  - "Logout revokes only the current session row and clears the product cookie."
  - "OAuth avatar URL is read-only bootstrap data; file upload stays deferred."
patterns-established:
  - "Private APIs depend on cookie hash lookup, never browser-supplied user ids."
requirements-completed: [AUTH-05, AUTH-06, PROF-01, PROF-02, TEST-02]
duration: 16 min
completed: 2026-04-27
---

# Phase 3 Plan 03: Current User And Me API Summary

**DB-backed current-user dependency with authenticated profile/wallet bootstrap and logout**

## Performance

- **Duration:** 16 min
- **Started:** 2026-04-27T14:30:00+03:00
- **Completed:** 2026-04-27T14:46:00+03:00
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `get_current_user` dependency that rejects missing, unknown, expired, and revoked sessions.
- Added `GET /api/v1/me` returning account, profile, and wallet summary from the database.
- Added `PATCH /api/v1/me` for display-name update.
- Added `POST /api/v1/me/logout` to revoke the current session and clear the cookie.

## Task Commits

Implementation is included in `64a1cd4` (`feat(03): implement oauth session profile APIs`).

## Files Created/Modified

- `backend/app/services/current_user.py` - Cookie-to-session-to-user dependency.
- `backend/app/services/profiles.py` - Account/profile/wallet summary and display-name update service.
- `backend/app/api/v1/me.py` - Authenticated `/me`, display-name update, and logout routes.
- `backend/tests/test_current_user.py` - Auth boundary tests.
- `backend/tests/test_me_api.py` - `/me`, update, and logout tests.

## Decisions Made

- Auth failures use the existing stable error envelope with `AUTH_REQUIRED`, `SESSION_INVALID`, `SESSION_EXPIRED`, and `SESSION_REVOKED`.
- `/api/v1/me` response excludes token hashes and provider secrets.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope creep.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Phase 4 can build ledger APIs on top of authenticated users and trusted wallet summaries.

---
*Phase: 03-oauth-sessions-and-profile-bootstrap*
*Completed: 2026-04-27*
