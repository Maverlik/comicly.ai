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
    - backend/index.py
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
- Added backend Vercel config rooted at `backend/` with Python 3.12. During final CLI verification this was aligned to Vercel's zero-config FastAPI entrypoint shape: `backend/index.py` imports the FastAPI app from `backend/app/main.py`, and duration is left to the project runtime/settings where supported.
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
- Vercel CLI validation in Plan 08-04 required replacing the earlier `functions`/`routes` shape with zero-config FastAPI entrypoint detection.

## Self-Check

PASSED. Frontend deployment output is explicit and private-file safe; backend has a standalone Vercel/FastAPI config and Python 3.12 marker.
