# Phase 6 Validation Strategy

**Phase:** 06-production-ai-generation-pipeline
**Status:** ready

## Requirement Coverage

| Requirement | Planned Coverage |
|-------------|------------------|
| GEN-01 | Authenticated `POST /api/v1/generations` accepts a migration-compatible creator payload and invokes backend generation. |
| GEN-02 | Successful generation updates `comic_pages` with model, cost, status, generated timestamp, image URL, and storage key. |
| GEN-03 | Generated image data is copied to Vercel Blob rather than relying only on provider URLs/browser memory. |
| GEN-04 | Provider/storage failure leaves failed job/page state and refunds debited coins idempotently. |
| GEN-05 | OpenRouter client has timeout/error mapping, model allow-list validation, and fixture-backed response parsing tests. |
| GEN-06 | Protected `/api/v1/ai-text` keeps AI text assistance available with validated tasks and no client-side secrets. |
| GEN-07 | Generation response returns updated balance plus persisted job/page data needed by Phase 7 frontend integration. |
| TEST-05 | Automated tests cover OpenRouter parsing and generation failure modes using fixtures/fakes. |

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

- Phase 6 changes stay inside `backend/` and `.planning/`.
- Generation APIs are authenticated and owner-scoped.
- Billable generation requires `Idempotency-Key`.
- Retried generation requests do not double-charge.
- Successful generation returns a Blob `image_url`, not base64.
- Failed provider/storage operations refund once and leave auditable failed status.
- AI text assistance is available through protected backend API.

## Known Non-Goals

- Static creator/frontend integration.
- Full async polling/queue/worker pipeline.
- Real production deployment execution.
- Charging for AI text assistance.
