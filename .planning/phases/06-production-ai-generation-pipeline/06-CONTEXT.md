# Phase 6: Production AI Generation Pipeline - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 connects authenticated backend generation to OpenRouter, wallet debits/refunds, durable image storage, `generation_jobs`, persisted comic pages, and frontend-ready response data.

In scope: protected generation APIs, OpenRouter request/response handling, model allow-list validation, `Idempotency-Key` handling, wallet debit/refund integration, Vercel Blob storage for generated images, generation job audit/status records, page persistence updates, updated balance/page response payloads, and fixture-backed tests for provider parsing/failure modes.

Out of scope: frontend/root runtime changes, Phase 7 creator hydration, full async queue/worker implementation, real payment fulfillment, public gallery/sharing, admin tooling, and hard production deployment execution.

</domain>

<decisions>
## Implementation Decisions

### Generation API Contract
- **D-01:** Implement a new authenticated FastAPI API under `/api/v1/generations` or an equivalent REST-style v1 route chosen during planning.
- **D-02:** The frontend-facing request should be migration-compatible with the current creator/OpenRouter payload shape where practical, so Phase 7 can switch the static creator without rewriting product behavior.
- **D-03:** The response should return the created/updated `generation_job`, persisted `comic_page` data, and updated wallet balance in the same HTTP response.
- **D-04:** Do not directly replace the legacy root Node `/api/generate-comic-page` and `/api/ai-text` routes in Phase 6; root/frontend runtime migration remains Phase 7 unless separately approved.

### Synchronous MVP Flow
- **D-05:** Use synchronous generation for MVP within Vercel Function duration limits.
- **D-06:** Expected flow: frontend sends `POST /api/v1/generations`; backend creates `generation_job` pending/processing; backend debits coins; backend calls OpenRouter/model API; backend saves the image to Vercel Blob; backend updates job succeeded/failed; backend returns `image_url`, job data, page data, and balance in the same response.
- **D-07:** `generation_jobs` must still be structured so the system can later move to async polling, queue, or worker execution without redesigning wallet/comic/page persistence.
- **D-08:** If OpenRouter/model generation often exceeds Vercel limits, a later phase should switch to async polling plus queue/worker.

### Image Storage
- **D-09:** Use Vercel Blob public storage for MVP generated image persistence.
- **D-10:** Backend must copy/store the generated image into Blob and persist both `image_url` and `storage_key` on the page record.
- **D-11:** Do not return large base64 payloads to the frontend. Return a durable `image_url`.
- **D-12:** Implementation must account for Vercel request/response body limits and avoid large response bodies.
- **D-13:** Keep storage integration behind a service boundary so Vercel Blob can later be swapped for S3, Cloudflare R2, or another object store without rewriting generation business logic.

### Coin Charge And Failure Semantics
- **D-14:** `Idempotency-Key` is required for billable generation requests.
- **D-15:** Backend debits before calling OpenRouter, using the Phase 4 wallet service primitives.
- **D-16:** If OpenRouter or Blob storage fails after debit, backend records a failed job/page state and performs an idempotent refund.
- **D-17:** Duplicate/retried requests with the same idempotency key must not double-charge.
- **D-18:** Insufficient balance should return the existing typed wallet error and should not create a successful debit.

### Model Policy
- **D-19:** Frontend may send `model_id`.
- **D-20:** Backend validates `model_id` against a server-side allow-list.
- **D-21:** If `model_id` is allowed, use it.
- **D-22:** If `model_id` is missing, use the env default model.
- **D-23:** If `model_id` is present but not allowed, return typed error `MODEL_NOT_ALLOWED`.
- **D-24:** Do not allow arbitrary client-provided model ids.

### AI Text Assistance
- **D-25:** Port AI text assistance to a protected `/api/v1/ai-text` or equivalent v1 route in Phase 6.
- **D-26:** Keep AI text free for MVP: validate task/payload, call OpenRouter server-side, and do not create generation jobs or wallet transactions for text assistance yet.
- **D-27:** Preserve current AI text tasks where practical: story enhancement, dialogue, captions, and scene suggestions.

### OpenRouter Safety
- **D-28:** OpenRouter credentials remain server-side via env.
- **D-29:** OpenRouter calls need timeout handling, safe error mapping, model allow-list validation, and fixture-backed response parsing tests.
- **D-30:** Provider responses should be normalized by service code before routes build API responses.

### the agent's Discretion
- Exact route names and request/response model names, as long as the route is under `/api/v1`, authenticated, and migration-compatible for Phase 7.
- Exact `generation_jobs` status strings, as long as they cover pending/processing/succeeded/failed and are documented/test-covered.
- Exact internal service split between OpenRouter client, storage client, generation orchestration, and page update helpers.
- Whether page creation is implicit during generation or requires an existing page, as long as owner scoping and frontend-ready response data are preserved.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source Of Truth
- `backend/BACKEND_TZ.md` - backend source-of-truth specification, especially generation business logic, coin debit/refund rules, comic history, safety/reliability, and env requirements.

### Project Requirements
- `.planning/PROJECT.md` - project constraints: server-side secrets, DB-authoritative wallet, durable comic history, backend-only phase boundaries.
- `.planning/REQUIREMENTS.md` - GEN-01 through GEN-07 and TEST-05 requirement definitions.
- `.planning/ROADMAP.md` - Phase 6 goal, success criteria, dependency on Phase 5, and Phase 7 frontend boundary.
- `.planning/STATE.md` - current phase position and continuity notes.

### Prior Phase Outputs
- `.planning/phases/02-data-and-payment-foundation/02-CONTEXT.md` - Vercel-first, Neon/serverless, synchronous MVP generation, and generation job schema decisions.
- `.planning/phases/04-wallet-ledger-and-coin-safety/04-CONTEXT.md` - debit-before-generation, refund, and idempotency policy.
- `.planning/phases/04-wallet-ledger-and-coin-safety/04-VERIFICATION.md` - wallet service primitives and behavior already verified.
- `.planning/phases/05-private-comic-persistence/05-CONTEXT.md` - page persistence shape and owner-scoped comic/page boundaries.
- `.planning/phases/05-private-comic-persistence/05-VERIFICATION.md` - private comic/page APIs and owner-scoping already verified.

### Provider And Storage Docs
- `https://openrouter.ai/docs/api-reference/chat-completion` - OpenRouter Chat Completions API contract.
- `https://openrouter.ai/docs/features/multimodal/images` - OpenRouter image/multimodal response shapes to normalize.
- `https://vercel.com/docs/vercel-blob` - Vercel Blob storage overview.
- `https://vercel.com/docs/vercel-blob/server-upload` - server-side Blob upload pattern.
- `https://vercel.com/docs/storage/vercel-blob/usage-and-pricing` - Hobby/free Blob limits and overage behavior.
- `https://vercel.com/docs/functions/configuring-functions/duration` - Vercel Function duration configuration and limits.
- `https://vercel.com/docs/functions/limitations` - request/response/body/filesystem/runtime constraints.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/current_user.py` - authenticate generation and AI text routes.
- `backend/app/services/wallets.py` - use `debit_generation_cost`, `refund_generation_debit`, and idempotency behavior for billable generation.
- `backend/app/services/comics.py` - use owner-scoped comic/page helpers or extend with generation-specific page update helpers.
- `backend/app/models/generation.py` - existing `GenerationJob` model already contains user/comic/scene/page references, status, job type, prompt, model, provider, cost, request/response payloads, and error fields.
- `backend/app/models/comic.py` - `ComicPage` already stores status, model, coin cost, image URL, storage key, dimensions, scene link, and generated timestamp.
- `backend/app/core/config.py` - already holds generation costs; Phase 6 should add OpenRouter/storage/model settings here.
- `backend/app/core/errors.py` - use `ApiError` and stable JSON error envelope.

### Established Patterns
- Business APIs live under `/api/v1`.
- Route handlers stay thin and delegate business logic to services.
- Authenticated APIs use `get_current_user`.
- Tests use in-memory SQLite for service/API behavior plus fixture-backed provider parsing tests.
- Backend-only phases must not modify frontend/root runtime files without explicit approval.

### Integration Points
- New generation routes should connect authenticated users, owner-scoped comics/pages, wallet debit/refund, OpenRouter, Blob storage, and `generation_jobs`.
- Successful generation should update `comic_pages` so Phase 7 can reload generated pages through the existing `/api/v1/comics/{id}` detail endpoint.
- AI text route should reuse the current Node prompt/task behavior where practical, but live under protected FastAPI v1 APIs.

</code_context>

<specifics>
## Specific Ideas

- User selected all recommended MVP choices: new protected v1 generation API, Vercel Blob image persistence, debit-before-generation with idempotent refund, synchronous MVP request with `generation_jobs`, protected free AI text route, and server-side model allow-list.
- User explicitly expects `POST /api/v1/generations` to be synchronous for MVP and return `image_url/job/balance` in the same HTTP response.
- User explicitly does not want large base64 payloads returned to the frontend.
- User wants `MODEL_NOT_ALLOWED` when a provided `model_id` is not on the allow-list.

</specifics>

<deferred>
## Deferred Ideas

- Async polling, queue, or worker-based generation - defer until generation regularly exceeds Vercel limits or UX requires background operation.
- Phase 7 frontend integration - later phase.
- Swapping Vercel Blob for S3/R2 - future portability option if cost/limits require it.
- Charging for AI text assistance - defer; MVP text help remains free.
- Public gallery/sharing/collaboration/admin features - out of v1 scope unless roadmap changes.

</deferred>

---

*Phase: 06-production-ai-generation-pipeline*
*Context gathered: 2026-04-28*
