# Phase 6 Research: Production AI Generation Pipeline

**Phase:** 06-production-ai-generation-pipeline
**Status:** ready
**Source of truth:** backend/BACKEND_TZ.md and 06-CONTEXT.md

## Current Backend Surface

- Phase 3 provides `get_current_user` and DB-backed product sessions.
- Phase 4 provides wallet debit/refund primitives with required `Idempotency-Key` for billable operations.
- Phase 5 provides owner-scoped comic/page persistence and API responses that Phase 6 can update after generation.
- `GenerationJob` already has user/comic/scene/page refs, status, prompt, model, provider, cost, request/response payloads, and error fields.
- Current root `server.js` has the legacy OpenRouter prompt construction, text tasks, image URL extraction, and allow-list shape to port into backend services.

## Provider And Storage Notes

- OpenRouter image generation uses `/api/v1/chat/completions` with `modalities`; image-capable models may return generated images in `choices[0].message.images` and may also include text content.
- OpenRouter docs recommend checking for image output capability and handling missing images as an error.
- Vercel Blob server uploads are available to Python through `vercel.blob.AsyncBlobClient`; the runtime expects `BLOB_READ_WRITE_TOKEN`.
- Vercel Functions have request/response payload limits, so Phase 6 must not return base64 image data to the frontend. The backend should store the generated image in Blob and return the Blob URL.
- Vercel Function max duration can support a synchronous MVP, but the job schema should remain ready for async polling later.

## Schema Gap

`generation_jobs` needs one more field for Phase 6 correctness:

- `idempotency_key` should be persisted and unique enough to replay a generation request without creating another provider call or wallet debit.

The planner should add a small Alembic migration and model/test coverage for this field. A user-scoped unique constraint is preferable if compatible with the existing schema; a globally unique key is acceptable if service-level conflict behavior is explicit.

## Recommended Implementation Shape

Plan generation in layers:

1. Settings/schema foundation for OpenRouter, model allow-list, Blob token, timeouts, and generation idempotency.
2. Provider/storage adapters with fakeable interfaces and fixture-backed parsing tests.
3. Generation orchestration service that coordinates owned comic/page state, generation job state, wallet debit/refund, OpenRouter, and Blob upload.
4. Authenticated API routes for synchronous `POST /api/v1/generations` and protected free AI text.
5. Docs and full gates.

The service should create/update job/page state before and after side effects so failures leave an auditable record. Provider/storage failures after debit should call the Phase 4 refund primitive with a deterministic refund idempotency key.

## API Shape To Plan

Recommended routes:

- `POST /api/v1/generations` - authenticated full-page generation.
- `GET /api/v1/generations/{job_id}` - optional lightweight status/detail endpoint if cheap; useful for future polling compatibility.
- `POST /api/v1/ai-text` - authenticated free text assistance for `enhance`, `dialogue`, `caption`, and `scenes`.

Generation request should include:

- `comic_id`
- optional `scene_id`
- `page_number`
- `story`
- optional `characters`, `style`, `tone`, `selected_scene`, `scenes`, `dialogue`, `caption`, `layout`
- optional `model_id`

Generation response should include:

- `job`
- `page`
- `balance`
- no large base64 content

## Validation Architecture

Phase 6 validation should prove the real product flow without live provider calls:

- Successful generation debits once, records a job, stores a Blob URL/storage key, updates page metadata, and returns updated balance.
- Retrying the same `Idempotency-Key` replays the same logical result without a second debit/provider call.
- Provider failure after debit records failed status and refunds once.
- Blob failure after debit records failed status and refunds once.
- Insufficient balance creates no successful debit and no successful page.
- Disallowed models return `MODEL_NOT_ALLOWED`.
- AI text route is authenticated, validates task/payload, and keeps secrets server-side.
- OpenRouter response parsing is covered by fixtures for image URL/data URL and missing-image failure.

## Non-Goals

- Frontend/root runtime changes.
- Full async queue/worker execution.
- Real payment/provider webhook work.
- Public sharing/gallery/admin features.
- Returning provider base64 payloads to the browser.

## Official References

- OpenRouter Chat Completions: https://openrouter.ai/docs/api-reference/chat-completion
- OpenRouter image generation: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
- Vercel Blob server uploads: https://vercel.com/docs/vercel-blob/server-upload
- Vercel Blob usage/pricing: https://vercel.com/docs/storage/vercel-blob/usage-and-pricing
- Vercel Function limits: https://vercel.com/docs/functions/limitations
- Vercel Function max duration: https://vercel.com/docs/functions/configuring-functions/duration
