---
phase: 08-deployment-and-operations
plan: 01
subsystem: deployment-config
status: complete
key-files:
  created:
    - vercel.json
    - scripts/build-frontend.mjs
    - backend/vercel.json
    - backend/.python-version
    - tests/phase8-deploy-config.test.mjs
  modified:
    - .gitignore
    - package.json
    - backend/README.md
metrics:
  tests_run: 2
---

# Plan 08-01 Summary - Vercel Deployment Config And Static Safety

## Completed

- Added a root Vercel config that builds an explicit `dist/` output using `npm run build:frontend`.
- Added `scripts/build-frontend.mjs`, which copies only allow-listed public frontend files and assets.
- Added backend Vercel config rooted at `backend/`, routing requests to `app/main.py` and setting `maxDuration` to 300 seconds.
- Added `backend/.python-version` with Python 3.12.
- Added deployment config contract tests for static output safety, backend config shape, and env example secret checks.
- Documented the Vercel deployment boundary in `backend/README.md`.

## Verification

| Command | Result |
| --- | --- |
| `node --test tests/phase8-deploy-config.test.mjs` | passed |
| `npm run build:frontend` | passed |

## Deviations

- Added `.gitignore` entry for `dist/`, which was not listed in the plan file but is required so the generated frontend deployment output does not pollute the worktree.
- Full backend gates are deferred to later Phase 8 plans/final verification because Plan 08-01 only touched deployment config/docs and root static tests.

## Self-Check

PASSED. Frontend deployment output is explicit and private-file safe; backend has a standalone Vercel/FastAPI config and Python 3.12 marker.
