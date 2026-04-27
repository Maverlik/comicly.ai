# Phase 4 Research: Wallet Ledger And Coin Safety

**Phase:** 04-wallet-ledger-and-coin-safety
**Status:** ready
**Source of truth:** backend/BACKEND_TZ.md

## Current Backend Surface

- Phase 2 already created `wallets` and `wallet_transactions` tables.
- `wallets.user_id` is unique and `wallets.balance` has a non-negative check.
- `wallet_transactions` records `amount`, `balance_after`, `reason`, references, and a unique nullable `idempotency_key`.
- Phase 3 bootstrap creates a wallet and starter grant transaction on first login.
- `/api/v1/me` returns the authoritative wallet balance for the authenticated user.
- Business APIs are under `/api/v1`; health endpoints remain unprefixed.

## Backend TZ Requirements

The wallet must be the database source of truth. Browser-sent balances, owner ids, costs, and payment state are not trusted.

Relevant requirements for this phase:

- Coin state is authoritative in the database.
- Every grant, debit, refund, and adjustment is represented as an auditable transaction row.
- Full page generation costs 20 coins and scene regeneration costs 4 coins, both controlled by backend config.
- Insufficient funds must return a clear machine-readable error.
- Retries, double-clicks, and repeated requests must not double debit the user.
- Failed generation must not lose coins; the backend must support a coherent refund/no-spend path.

## Design Decisions For Planning

### Keep Phase 4 Backend-Only

Phase 4 should not modify frontend or root runtime files. It provides wallet primitives and a read-only wallet API that later generation and frontend phases can consume.

### Add Service Layer Before Generation Integration

The safest Phase 4 implementation target is a wallet service module that owns:

- wallet summary reads;
- grants and adjustments;
- billable debits using server-side costs;
- refund transactions linked to prior debits;
- idempotency key lookup and replay;
- insufficient balance errors;
- transaction ordering for recent history.

Phase 6 will call these primitives around OpenRouter generation/jobs. Phase 4 should not keep a database transaction open while any network generation request runs.

### Use Existing Schema Unless A Test Proves A Gap

The existing schema already has the key constraints Phase 4 needs: non-negative wallet balance, non-zero transaction amounts, and unique idempotency keys. No planned migration is required. If execution discovers a missing backend-only constraint or index required for correctness, it can add an Alembic migration inside `backend/` only.

### Serverless-Friendly Idempotency

Billable wallet operations require an `Idempotency-Key` header in future public endpoints. In Phase 4 the service should enforce the same rule for debit/refund primitives and tests should prove that duplicate keys return one logical result.

### Concurrency Strategy

PostgreSQL runtime should use row-level wallet locking or an equivalent atomic update strategy when changing balances. SQLite tests can use a deterministic fallback while still proving that duplicate idempotency keys and insufficient balances do not create negative balances.

## Non-Goals

- Real OpenRouter generation integration.
- Public debit/generation API endpoints.
- Frontend balance rendering.
- Real payment fulfillment.
- Full paginated transaction history.
- Object storage or durable image storage.

