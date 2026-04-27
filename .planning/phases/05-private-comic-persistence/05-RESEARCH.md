# Phase 5 Research: Private Comic Persistence

**Phase:** 05-private-comic-persistence
**Status:** ready
**Source of truth:** backend/BACKEND_TZ.md

## Current Backend Surface

- Phase 2 created base `comics`, `comic_scenes`, `comic_pages`, and `generation_jobs` tables.
- Phase 3 provides authenticated `get_current_user` and DB-backed sessions.
- Phase 4 provides wallet accounting, but Phase 5 must not connect generation or debits.
- Existing API patterns use FastAPI routers under `/api/v1`, thin handlers, service modules, Pydantic response models, and SQLite-backed async tests.

## Schema Gap

The existing Phase 2 schema is a useful base but does not yet match the locked Phase 5 context:

- `comics` has `title`, `status`, `style_preset`, but not first-class `story`, `characters`, `tone`, or `selected_model`.
- `comic_scenes` has `prompt`, `script_text`, `metadata_json`, but not first-class `title`, `dialogue`, or `caption`.
- `comic_pages` has `page_number`, `image_url`, `storage_key`, dimensions, and `status`, but not `model`, `coin_cost`, or `generated_at`.

Phase 5 should add a backend-only Alembic migration and model updates rather than storing the MVP contract mostly in JSON.

## API Shape To Plan

Recommended route surface:

- `POST /api/v1/comics` - create a private draft.
- `GET /api/v1/comics` - list current user's non-archived comics in compact form.
- `GET /api/v1/comics/{comic_id}` - full detail with scenes and pages.
- `PATCH /api/v1/comics/{comic_id}` - update metadata/status, including archive.
- Scene and page mutation routes under a scoped comic path, for example:
  - `PUT /api/v1/comics/{comic_id}/scenes` - replace scene list with stable ordered structured scenes.
  - `PUT /api/v1/comics/{comic_id}/pages` - replace or upsert persistence-only page records.

The exact child route split is agent discretion, but planning should preserve compact list plus full detail and avoid public generation/debit endpoints.

## Ownership Strategy

Every service query should scope by both object id and `current_user.user.id` through the parent comic. For scenes/pages, the service should first resolve the comic owned by the user, then mutate child rows only under that comic.

Expected stable error approach:

- anonymous requests use existing auth dependency errors;
- missing or foreign-owned comics return the same not-found style error to avoid leaking object existence;
- duplicate positions/page numbers should return stable validation/conflict errors if not caught by request validation.

## Testing Strategy

Plan tests should cover:

- schema/migration metadata for added first-class fields and constraints;
- create/update/archive/list/detail behavior for one user;
- scene ordering and full draft reload;
- page persistence records with status/model/cost/image fields;
- two-user ownership boundaries for list, detail, update, scene save, and page save;
- no frontend/root file changes;
- full backend gates.

## Validation Architecture

Phase 5 validation should prove goal achievement, not just endpoint existence:

- A user can create a draft with metadata, reload it by id, and see the same metadata.
- A user can save structured scenes and reload them in order.
- A user can save page records and reload their page metadata.
- A user's list excludes other users' comics and hides archived comics by default.
- Another user cannot access or mutate the first user's comic, scenes, or pages.
- Browser refresh/reopen is represented by `GET /api/v1/comics/{id}` returning enough detail to restore the draft.

## Non-Goals

- Frontend integration.
- OpenRouter generation calls.
- Wallet debits or refunds during generation.
- Durable object storage.
- Hard delete.
- Optimistic locking/version conflicts.
- Public gallery, sharing, collaboration, or search.

