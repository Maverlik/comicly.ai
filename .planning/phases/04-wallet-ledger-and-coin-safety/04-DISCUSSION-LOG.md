# Phase 4: Wallet Ledger And Coin Safety - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-27T18:10:55+03:00
**Phase:** 4-Wallet Ledger And Coin Safety
**Areas discussed:** Wallet API surface, debit/refund semantics, idempotency policy, phase scope

---

## Wallet API Surface

| Option | Description | Selected |
|--------|-------------|----------|
| Balance + recent transactions | `GET /api/v1/wallet` returns balance plus recent ledger rows. | ✓ |
| Balance only | Keep history internal until later UI/admin work. | |
| Full paginated history | Add complete transaction history API now. | |

**User's choice:** Balance + recent transactions.
**Notes:** User agreed with the recommended MVP path.

---

## Debit And Refund Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Debit before generation + refund on failure | Best protection against parallel generation/double-click problems and fits future jobs. | ✓ |
| Debit only after success | Simpler refund story, but weaker reservation/blocking model. | |
| Hold/capture/refund reservation model | Strongest long-term ledger model, heavier than needed for MVP. | |

**User's choice:** Debit before generation + refund on failure.
**Notes:** Phase 4 should implement primitives only; real generation integration remains Phase 6.

---

## Idempotency Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Required `Idempotency-Key` header | Missing key returns `400 IDEMPOTENCY_KEY_REQUIRED`; retries cannot double-charge. | ✓ |
| Backend-generated key fallback | Easier client integration, weaker retry semantics. | |
| Optional key for MVP | Lowest implementation cost, not strong enough for money-like operations. | |

**User's choice:** Required `Idempotency-Key` header.
**Notes:** Stable error code is locked for missing keys.

---

## Phase Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Wallet ledger foundation only | API, services, insufficient funds, idempotency, concurrency tests. | ✓ |
| Add mock billable endpoint | Adds a test route-like surface for debits. | |
| Connect real generation now | Mixes Phase 4 with Phase 6. | |

**User's choice:** Wallet ledger foundation only.
**Notes:** No frontend/root changes and no OpenRouter integration in Phase 4.

---

## the agent's Discretion

- Exact service/function names.
- Exact recent transaction limit.
- Test implementation details for race/concurrency coverage.

## Deferred Ideas

- Full paginated wallet history.
- Real generation debit integration.
- Payment webhook fulfillment.
- Admin adjustment UI.
