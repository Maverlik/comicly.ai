# Phase 3 Discussion Log

**Date:** 2026-04-27
**Mode:** batch
**Phase:** 03-oauth-sessions-and-profile-bootstrap

## Context Loaded

- Phase 2 is verified complete and provides SQLAlchemy/Alembic tables for users, provider identities, profiles, sessions, wallets, wallet transactions, coin packages, payments, comics, and generation jobs.
- Backend remains standalone FastAPI in `backend/`.
- `backend/BACKEND_TZ.md` remains the source-of-truth backend requirements document.
- Phase 3 is scoped to OAuth, sessions, profile bootstrap, and authenticated account/profile/wallet summary APIs.

## User Decisions

1. Redirect after successful login should go to `comicly.ai/create.html`.
2. Google/Yandex accounts should be linked by verified email so one person does not get duplicate accounts across providers.
3. Avatar upload should not be implemented in Phase 3. Use OAuth `avatar_url` only; real upload waits for a storage provider decision.
4. Session lifetime should be 30 days.
5. Phase 3 is backend API-only. Do not touch frontend; at most prepare redirect URL through env/config.

## Result

Created `03-CONTEXT.md` for downstream research and planning.
