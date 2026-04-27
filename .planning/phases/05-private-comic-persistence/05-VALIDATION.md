# Phase 5 Validation Strategy

**Phase:** 05-private-comic-persistence
**Status:** ready

## Requirement Coverage

| Requirement | Planned Coverage |
|-------------|------------------|
| COMIC-01 | Comic create/update APIs persist private draft metadata: title, story, characters, style, tone, selected model, and status. |
| COMIC-02 | Scene persistence APIs save/reload title, description, dialogue, caption, and stable order. |
| COMIC-03 | Page persistence APIs save/reload page number, status, model, cost, image location, and timestamps. |
| COMIC-04 | Current user can list compact comic history and open one full-detail comic by id. |
| COMIC-05 | Services and API tests enforce owner scope for list, detail, update, scene, and page operations. |
| COMIC-06 | Full-detail response contains enough metadata, scenes, and pages to restore a draft after browser refresh/reopen. |
| TEST-04 | Automated tests include at least two users and prove comic ownership boundaries. |

## Gates

Run from `backend/`:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Boundary check from repository root:

```powershell
git diff --name-only -- server.js package.json index.html create.html scripts styles.css creator.css .env.example
```

## Phase-Level Acceptance

- Phase 5 changes stay inside `backend/` and `.planning/`.
- Comic persistence APIs are authenticated and private by default.
- Archived comics are hidden from default list responses.
- Scene/page data can be saved and reloaded without relying on browser memory.
- No OpenRouter generation, wallet debit, frontend integration, or storage upload is implemented.

## Known Non-Goals

- Bulk autosave endpoint.
- Hard delete.
- Optimistic locking.
- Search/filtering.
- Public/social comic features.
- Real generation pipeline.

