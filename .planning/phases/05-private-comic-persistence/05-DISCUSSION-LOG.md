# Phase 5: Private Comic Persistence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-27T20:37:43+03:00
**Phase:** 5 - Private Comic Persistence
**Areas discussed:** draft save model, comic metadata storage, scene shape, page persistence, delete/archive, list/detail API shape, concurrent edits

---

## Draft Save Model

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit CRUD | Create comic, update comic metadata, replace/update scenes/pages separately. | yes |
| Bulk autosave | One endpoint upserts the whole creator state in one request. | |
| Both | CRUD plus bulk save. | |

**User's choice:** all recommended options, including Explicit CRUD.
**Notes:** Keep the API contract clear and backend-owned before frontend integration.

---

## Comic Metadata Storage

| Option | Description | Selected |
|--------|-------------|----------|
| First-class columns | Store `story`, `characters`, `style`, `tone`, and `selected_model` as normal fields; JSON only for extras. | yes |
| Mostly JSON | Store most metadata in `metadata_json`. | |

**User's choice:** all recommended options, including First-class columns.
**Notes:** Prefer validation and clear persistence over flexible blobs.

---

## Scene Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Structured scenes | Store `title`, `description/prompt`, `dialogue`, `caption`, and `position`. | yes |
| Minimal fields | Store only `prompt/script_text/position`, rest in JSON. | |
| Raw blob | Store frontend scene blob. | |

**User's choice:** all recommended options, including Structured scenes.
**Notes:** Scene data should be reloadable and editable without depending on frontend memory shape.

---

## Page Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Page records and APIs | Store/update page records without real generation. | yes |
| Service only | Prepare service/schema but no public page APIs. | |
| Defer pages | Only comics/scenes in Phase 5. | |

**User's choice:** all recommended options, including Page records and APIs.
**Notes:** Phase 5 persists page state, Phase 6 later performs generation.

---

## Delete And Archive

| Option | Description | Selected |
|--------|-------------|----------|
| Soft archive | Support archived status and hide archived comics from default lists. | yes |
| Hard delete | Add hard delete endpoint. | |
| No archive/delete | Leave removal behavior for later. | |

**User's choice:** all recommended options, including Soft archive.
**Notes:** MVP should avoid accidental data loss.

---

## List And Detail API Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Compact list + full detail | List returns compact comics; detail returns scenes/pages. | yes |
| Full tree list | List embeds scenes/pages for every comic. | |
| Compact + separate child APIs only | List compact, scenes/pages fetched only through separate endpoints. | |

**User's choice:** all recommended options, including Compact list + full detail.
**Notes:** Good fit for later history/reopen UX without heavy list responses.

---

## Concurrent Edits

| Option | Description | Selected |
|--------|-------------|----------|
| Last-write-wins | Simpler MVP behavior with `updated_at` returned. | yes |
| Optimistic locking | Version or timestamp conflicts return `409`. | |

**User's choice:** all recommended options, including Last-write-wins.
**Notes:** Conflict handling can evolve later if needed.

---

## the agent's Discretion

- Exact route split for scene/page mutation endpoints.
- Exact request/response model names.
- Exact service/module names.
- Exact implementation of scene replacement versus individual mutation operations.

## Deferred Ideas

- Bulk autosave endpoint.
- Hard delete.
- Optimistic locking.
- Full history search/filtering.
- Public/social comic features.

