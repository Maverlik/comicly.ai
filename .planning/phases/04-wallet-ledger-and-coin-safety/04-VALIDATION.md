# Phase 4 Validation Strategy

**Phase:** 04-wallet-ledger-and-coin-safety
**Status:** ready

## Requirement Coverage

| Requirement | Planned Coverage |
|-------------|------------------|
| WAL-01 | Authenticated `GET /api/v1/wallet` returns the database wallet balance and recent history. |
| WAL-02 | Wallet service records every grant, debit, refund, and adjustment as a transaction row. |
| WAL-03 | Insufficient funds return `INSUFFICIENT_COINS` and do not create debit rows. |
| WAL-04 | Full-page debit service uses backend generation cost setting: 20 coins. |
| WAL-05 | Scene-regeneration debit service uses backend generation cost setting: 4 coins. |
| WAL-06 | Billable service operations require idempotency keys and duplicate keys do not double-charge. |
| WAL-07 | Balance mutations are race-safe and cannot produce negative balances under concurrent requests. |
| TEST-03 | Tests cover service correctness, wallet API, insufficient funds, idempotency, refund path, and concurrent debit protection. |

## Gates

Run from `backend/`:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Boundary check from repository root:

```powershell
git diff --name-only -- server.js package.json index.html create.html scripts styles.css creator.css
```

## Phase-Level Acceptance

- Wallet balance is read from the database, not from browser input.
- Every balance change goes through a ledger transaction.
- Billable operations are idempotent and cannot spend below zero.
- Duplicate idempotency keys return/reuse one logical wallet operation.
- Failed future generation can be represented by an automatic refund transaction.
- Phase remains backend API-only and does not change frontend/root runtime files.

## Known Non-Goals

- Public generation/debit endpoint integration.
- OpenRouter calls.
- Frontend balance display.
- Full transaction-history pagination.
- Real payment checkout/webhooks.
