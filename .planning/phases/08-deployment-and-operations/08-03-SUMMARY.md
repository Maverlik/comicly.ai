---
phase: 08-deployment-and-operations
plan: 03
subsystem: operations-docs
status: complete
key-files:
  created:
    - backend/docs/deployment.md
    - backend/scripts/smoke_production.py
  modified:
    - .env.example
    - backend/.env.example
    - backend/README.md
    - tests/phase8-deploy-config.test.mjs
metrics:
  tests_run: 4
---

# Plan 08-03 Summary - Environment Docs, Runbook, And Smoke Tooling

## Completed

- Replaced the garbled root `.env.example` with a safe placeholder-only local/static frontend example.
- Expanded `backend/.env.example` production notes for CORS, callbacks, local Docker DB, and security controls.
- Added `backend/docs/deployment.md` with the Vercel-first production runbook:
  - two Vercel projects;
  - Neon pooled runtime URL plus direct migration URL;
  - Vercel Blob;
  - OAuth callback URLs;
  - CORS/cookie settings;
  - migrations and seed commands;
  - smoke/manual verification split.
- Added `backend/scripts/smoke_production.py` for repeatable frontend/API smoke checks.
- Expanded Phase 8 deploy config tests to cover the runbook and smoke helper.

## Verification

| Command | Result |
| --- | --- |
| `node --test tests/phase8-deploy-config.test.mjs` | passed |
| `python -m ruff check scripts/smoke_production.py` | passed with bundled Python |
| `python -m ruff format --check scripts/smoke_production.py` | passed with bundled Python |
| `python backend/scripts/smoke_production.py --api-base-url http://localhost:8000 --frontend-url http://localhost:3000 --skip-ready` | passed |

## Deviations

- Local smoke used `--skip-ready` because this check is about the smoke helper shape and currently running services; final readiness is covered again in Plan 08-04.
- Used bundled Codex Python runtime because the Windows `python` app alias is not available in this shell.

## Self-Check

PASSED. Env examples are placeholder-only, the runbook covers local and production operations, and smoke tooling separates automated checks from live provider-secret-dependent checks.
