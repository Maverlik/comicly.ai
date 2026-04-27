# Phase 5: Private Comic Persistence - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 adds backend API-only persistence for private comics, scenes, and pages owned by the authenticated user. It must let users create, save, list, reopen, and continue their own comic drafts/history through FastAPI and PostgreSQL.

Out of scope for Phase 5: frontend/root runtime changes, OpenRouter calls, real image generation, wallet debits during generation, object storage upload/copying, public gallery/feed, collaboration, sharing, and admin tools.

</domain>

<decisions>
## Implementation Decisions

### Draft Save Model
- **D-01:** Use explicit REST-style CRUD rather than one bulk autosave endpoint.
- **D-02:** Phase 5 should support creating a comic, updating comic metadata, and creating/updating/replacing scenes/pages through clear backend APIs.
- **D-03:** Do not add a one-request whole-creator-state autosave endpoint in Phase 5.

### Comic Metadata Storage
- **D-04:** Store core comic draft metadata in normal database columns: `story`, `characters`, `style`, `tone`, and `selected_model`.
- **D-05:** Use JSON only for optional/future extras that do not need first-class validation/querying yet.
- **D-06:** If the existing Phase 2 schema lacks these first-class fields, Phase 5 should add a backend Alembic migration inside `backend/`.

### Scene Shape
- **D-07:** Store scenes as structured fields: `title`, `description` or prompt, `dialogue`, `caption`, and stable `position`.
- **D-08:** Avoid storing the whole frontend scene blob as the primary representation.
- **D-09:** Scene ordering must be stable and owner-scoped through the parent comic.

### Page Persistence
- **D-10:** Phase 5 should include page records and page APIs even though real generation remains Phase 6.
- **D-11:** Page records should support `page_number`, `status`, `model`, `coin_cost`, `image_url`, `storage_key`, dimensions, and timestamps.
- **D-12:** Page APIs should be persistence-only in Phase 5: create/update/list/reload records, but no OpenRouter generation and no wallet debit integration.

### Delete And Archive
- **D-13:** Prefer soft archive over hard delete for MVP.
- **D-14:** Support an `archived` comic status or equivalent update path so archived comics can be hidden from default lists.
- **D-15:** Do not add hard-delete endpoints in Phase 5.

### List And Detail API Shape
- **D-16:** `GET /api/v1/comics` should return a compact list of the current user's comics, without embedding full scene/page trees.
- **D-17:** `GET /api/v1/comics/{id}` should return full comic detail, including scenes and pages.
- **D-18:** The list endpoint should be enough for history/reopen UX later, while detail endpoint restores an editable draft.

### Concurrent Edits
- **D-19:** Use last-write-wins for MVP.
- **D-20:** Return `updated_at` timestamps in responses so later frontend work can display freshness or evolve toward optimistic locking.
- **D-21:** Do not implement version conflict detection in Phase 5 unless planning finds an unavoidable backend correctness issue.

### Ownership And Privacy
- **D-22:** Every comic, scene, and page API must be authenticated and scoped to `current_user`.
- **D-23:** Users must not be able to list, open, update, archive, or save pages/scenes for another user's comic.
- **D-24:** Tests must include at least two users proving ownership boundaries.

### the agent's Discretion
- Exact route split for scene/page mutation endpoints, as long as list/detail contracts remain clear and REST-like.
- Exact Pydantic response/request model names.
- Whether scene replacement is implemented as a bulk replace endpoint or individual create/update/delete-like operations, as long as stable ordering and reload behavior are covered.
- Exact enum strings beyond the source-of-truth set `draft`, `generated`, `failed`, `archived` or close equivalents.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source Of Truth
- `backend/BACKEND_TZ.md` - backend source-of-truth specification, especially comic history requirements around project title, source story, characters, style, tone, page list, generated page metadata, statuses, and owner privacy.

### Project Requirements
- `.planning/PROJECT.md` - project constraints: backend milestone, private comic history, DB-authoritative persistence, server-side trust boundaries.
- `.planning/REQUIREMENTS.md` - COMIC-01 through COMIC-06 and TEST-04 requirement definitions.
- `.planning/ROADMAP.md` - Phase 5 goal, success criteria, dependency on Phase 4, and future Phase 6/7 boundaries.
- `.planning/STATE.md` - current phase position and continuity notes.

### Prior Phase Outputs
- `.planning/phases/02-data-and-payment-foundation/02-01-SUMMARY.md` - existing comic, scene, page, and generation job schema surface.
- `.planning/phases/02-data-and-payment-foundation/02-02-SUMMARY.md` - migration/constraint context for comics and pages.
- `.planning/phases/03-oauth-sessions-and-profile-bootstrap/03-VERIFICATION.md` - authenticated current-user/session foundation.
- `.planning/phases/04-wallet-ledger-and-coin-safety/04-VERIFICATION.md` - wallet/generation cost foundation that Phase 6 will connect after Phase 5 persistence exists.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/current_user.py` - use `get_current_user` for all private comic APIs.
- `backend/app/core/errors.py` - use `ApiError` and existing error envelope for not found/ownership/validation failures.
- `backend/app/api/v1/__init__.py` - register Phase 5 routers under `/api/v1`.
- `backend/app/models/comic.py` - existing `Comic`, `ComicScene`, and `ComicPage` models already provide base tables and ownership/ordering constraints.
- `backend/app/models/generation.py` - `GenerationJob` exists for Phase 6; Phase 5 should avoid doing generation work but may preserve page fields that later jobs connect to.

### Established Patterns
- Backend business APIs live under `/api/v1`.
- Route handlers should stay thin and delegate business logic to services.
- Tests use in-memory SQLite fixtures for service/API behavior and metadata tests for schema constraints.
- Backend-only phases must not modify frontend/root runtime files without explicit approval.

### Integration Points
- New comic APIs should build on the authenticated user/session foundation from Phase 3.
- Page persistence should prepare records that Phase 6 generation can later update with model, cost, image URL/storage key, status, and generation timestamps.
- `GET /api/v1/comics` and `GET /api/v1/comics/{id}` will become the Phase 7 frontend integration surface for history and draft reload.

</code_context>

<specifics>
## Specific Ideas

- User selected all recommended MVP options: explicit CRUD, first-class comic metadata columns, structured scenes, persistence-only page APIs, soft archive, compact list plus full detail, and last-write-wins concurrency.
- The guiding product behavior is "private history first": users should be able to save/reopen their own draft/comic data before generation is wired to real OpenRouter persistence.

</specifics>

<deferred>
## Deferred Ideas

- Whole-creator-state autosave endpoint - defer unless Phase 7 frontend integration proves it is simpler.
- Hard-delete endpoint - defer beyond MVP.
- Optimistic locking/version conflicts - defer until real concurrent editing pain appears.
- Full text search/filtering over comic history - defer beyond Phase 5.
- Public gallery/feed/sharing/collaboration - out of v1 scope unless roadmap changes.
- Real OpenRouter generation/page creation pipeline - Phase 6.
- Frontend creator hydration and history UI - Phase 7.

</deferred>

---

*Phase: 05-private-comic-persistence*
*Context gathered: 2026-04-27*

