# Phase 4: Wallet Ledger And Coin Safety - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 makes wallet balance and balance-changing operations authoritative, auditable, idempotent, and concurrency-safe in the FastAPI backend. It is backend API-only: no frontend/root runtime changes, no OpenRouter generation integration, and no real payment fulfillment.

</domain>

<decisions>
## Implementation Decisions

### Wallet API Surface
- **D-01:** Implement `GET /api/v1/wallet` for authenticated users.
- **D-02:** Response should include the authoritative wallet balance plus a short recent transaction list.
- **D-03:** Full paginated transaction history can be added later; Phase 4 should expose only enough history for MVP trust/debugging.

### Debit And Refund Semantics
- **D-04:** Use atomic debit-before-generation semantics for future billable generation.
- **D-05:** If downstream generation fails after a debit, backend must support an automatic refund transaction.
- **D-06:** Phase 4 implements the wallet service primitives and tests for debit/refund behavior; Phase 6 will connect those primitives to real OpenRouter generation and generation jobs.

### Idempotency Policy
- **D-07:** Billable wallet operations require an `Idempotency-Key` header.
- **D-08:** Missing idempotency key returns a stable `400 IDEMPOTENCY_KEY_REQUIRED` error.
- **D-09:** Retried requests with the same idempotency key must return one logical wallet operation and must not double-charge.

### Phase 4 Scope
- **D-10:** Keep Phase 4 as wallet ledger foundation only: balance/recent-history API, grant/debit/refund service, insufficient funds behavior, idempotency, and concurrency tests.
- **D-11:** Do not connect wallet debits to real generation routes in Phase 4.
- **D-12:** Do not change frontend/root runtime files in Phase 4.

### the agent's Discretion
- Exact internal service/function names.
- Exact recent transaction list limit, as long as it is small and documented/test-covered.
- Whether tests exercise concurrency with SQLite-safe patterns or Postgres-specific integration, as long as they prove the intended race-safety contract.

</decisions>

<specifics>
## Specific Ideas

- User approved the recommended MVP path: `1A, 2A, 3A, 4A`.
- The guiding product rule is trust over convenience: balance comes from DB, every balance change is a transaction row, and retries/double-clicks cannot double-charge.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/PROJECT.md` — project constraints: DB-authoritative coins, server-side secrets, backend-only phase boundaries.
- `.planning/REQUIREMENTS.md` — WAL-01 through WAL-07 and TEST-03 requirement definitions.
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, and dependency on Phase 3.
- `backend/BACKEND_TZ.md` — source-of-truth backend specification, especially sections on coin system, generation business logic, and safety/reliability.

### Prior Phase Outputs
- `.planning/phases/02-data-and-payment-foundation/02-01-SUMMARY.md` — wallet and transaction schema surface.
- `.planning/phases/02-data-and-payment-foundation/02-02-SUMMARY.md` — database constraints and migration context.
- `.planning/phases/03-oauth-sessions-and-profile-bootstrap/03-VERIFICATION.md` — authenticated user/session foundation that Phase 4 must build on.
- `.planning/phases/03-oauth-sessions-and-profile-bootstrap/03-03-SUMMARY.md` — `/api/v1/me` and current-user dependency context.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/current_user.py` — use `get_current_user` for authenticated wallet APIs.
- `backend/app/models/wallet.py` — existing `Wallet` and `WalletTransaction` models already include balance, amount, balance_after, reason, reference fields, and unique idempotency key.
- `backend/app/core/config.py` — generation costs and starter coins already exist as settings.
- `backend/app/core/errors.py` — use existing stable error envelope via `ApiError`.

### Established Patterns
- Backend APIs are mounted under `/api/v1`.
- Route tests use in-memory SQLite/SQLAlchemy fixtures where possible.
- Phase 3 services keep business logic out of route handlers; Phase 4 should follow that service pattern.
- Root/frontend files are out of scope unless explicitly approved.

### Integration Points
- `GET /api/v1/wallet` should connect to the existing auth dependency and wallet tables.
- Wallet service should become the future Phase 6 integration point for generation debit/refund.
- `/api/v1/me` already returns wallet balance; Phase 4 should keep it consistent with the ledger service behavior.

</code_context>

<deferred>
## Deferred Ideas

- Full paginated transaction history UI/API — later profile/frontend/admin work.
- Real OpenRouter generation debit integration — Phase 6.
- Payment webhook coin fulfillment — v2/payment phase, not Phase 4.
- Admin wallet adjustments UI — out of v1 scope unless roadmap changes.

</deferred>

---

*Phase: 04-wallet-ledger-and-coin-safety*
*Context gathered: 2026-04-27*
