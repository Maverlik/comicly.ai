---
phase: 04-wallet-ledger-and-coin-safety
plan: 01
status: complete
completed: 2026-04-27
---

# 04-01 Summary: Wallet Ledger Service

## Completed

- Added `backend/app/services/wallets.py` as the centralized wallet accounting service.
- Added grant, generation debit, generation refund, summary, idempotency replay, and insufficient-funds primitives.
- Used atomic wallet balance updates for debit/grant/refund mutations so concurrent debit attempts cannot spend below zero.
- Enforced `IDEMPOTENCY_KEY_REQUIRED` for billable debits and refunds.
- Returned `INSUFFICIENT_COINS` with status `409` when a wallet cannot cover a debit.
- Added focused wallet service tests for grants, configured generation costs, duplicate idempotency keys, insufficient funds, refunds, recent history, and concurrent debits.

## Verification

```powershell
C:\Users\ivan3\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests/test_wallet_service.py
```

Result: `9 passed`.

## Notes

- `python` on this machine currently resolves to the Windows Store alias, so verification used the bundled Codex Python runtime.
- No frontend/root runtime files were changed.

