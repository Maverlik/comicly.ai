# Phase 6: Production AI Generation Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 6 - Production AI Generation Pipeline
**Areas discussed:** Generation API contract, Image storage, Coin charge and failure semantics, Sync vs async, AI text assistance, Model policy

---

## Generation API Contract

| Option | Description | Selected |
|--------|-------------|----------|
| A | New authenticated `/api/v1/generations` or equivalent v1 route; migration-compatible payload; returns job, page, and balance. | yes |
| B | Directly port legacy `/api/generate-comic-page` and `/api/ai-text` contracts to FastAPI now. | |
| C | Async-only API with start job plus polling. | |

**User's choice:** A.
**Notes:** Preserve migration compatibility for later frontend integration without changing root/frontend runtime during Phase 6.

---

## Image Storage

| Option | Description | Selected |
|--------|-------------|----------|
| A | Use Vercel Blob public storage for MVP; backend stores generated image and persists `image_url`/`storage_key`. | yes |
| B | Temporarily store only the provider URL from OpenRouter. | |
| C | Store base64/image bytes in Postgres. | |

**User's choice:** A.
**Notes:** Do not return large base64 in API responses. Return durable `image_url`.

---

## Coin Charge And Failure Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| A | Require `Idempotency-Key`; create job/page state; debit before OpenRouter; refund idempotently on provider/storage failure. | yes |
| B | Charge only after successful generation. | |
| C | No coin debit in Phase 6. | |

**User's choice:** A.
**Notes:** Must not double-charge on retry/double click; failed generation leaves a correct failed status.

---

## Sync Vs Async

| Option | Description | Selected |
|--------|-------------|----------|
| A | Synchronous MVP request within Vercel limits, with `generation_jobs` as audit/status records. | yes |
| B | Start job plus polling from the beginning. | |
| C | Direct generation response without jobs. | |

**User's choice:** A.
**Notes:** User expects frontend to call `POST /api/v1/generations` and wait for the same HTTP response containing `image_url`, job data, and balance. Implementation must account for Vercel maxDuration and body limits. If generation frequently exceeds limits, later switch to async polling plus queue/worker.

---

## AI Text Assistance

| Option | Description | Selected |
|--------|-------------|----------|
| A | Port to protected `/api/v1/ai-text`; keep free for MVP; validate task/payload; no job record. | yes |
| B | Store text assistance in `generation_jobs` and charge scene regeneration cost. | |
| C | Leave AI text only in the legacy Node route until Phase 7. | |

**User's choice:** A.
**Notes:** Keep the current product tasks where practical: enhance, dialogue, caption, and scenes.

---

## Model Policy

| Option | Description | Selected |
|--------|-------------|----------|
| A | Server-side allow-list; frontend may send `model_id`; env default only when no model is supplied. | yes |
| B | Allow any client-provided model id. | |
| C | Ignore client model and always use one env default. | |

**User's choice:** A.
**Notes:** If `model_id` is present but not allowed, return typed error `MODEL_NOT_ALLOWED`.

---

## the agent's Discretion

- Exact route naming, as long as it stays under authenticated `/api/v1` and preserves the locked behavior.
- Exact internal service split for OpenRouter, Blob storage, generation orchestration, and page update helpers.
- Exact job status strings, as long as pending/processing/succeeded/failed are covered and testable.

## Deferred Ideas

- Async polling, queue, or worker-based generation if synchronous Vercel requests prove too slow.
- Charging for AI text assistance.
- Swapping Vercel Blob for another object store if free-tier/cost/limits become a problem.
