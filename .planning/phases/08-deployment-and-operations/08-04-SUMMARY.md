---
phase: 08-deployment-and-operations
plan: 04
subsystem: deployment-verification
status: complete-with-external-blockers
key-files:
  created:
    - .planning/phases/08-deployment-and-operations/08-REVIEW.md
    - .planning/phases/08-deployment-and-operations/08-VERIFICATION.md
    - .planning/phases/08-deployment-and-operations/08-04-SUMMARY.md
    - .vercelignore
    - backend/.gitignore
    - backend/.vercelignore
    - backend/index.py
    - backend/tests/test_db_health.py
  modified:
    - .gitignore
    - backend/app/db/health.py
    - backend/vercel.json
    - backend/docs/deployment.md
    - backend/README.md
    - tests/phase8-deploy-config.test.mjs
metrics:
  local_gates_passed: 7
  vercel_deploy_attempts: 4
---

# Plan 08-04 Summary - Deploy Attempt, Smoke Checks, Review, Verification

## Completed

- Ran local static, frontend build, Docker config, backend pytest, backend ruff lint, backend ruff format, and local smoke gates.
- Confirmed Vercel CLI authentication as user `d1sney`.
- Attempted root frontend deploy. The linked Vercel project exists but is currently blocked by Vercel Services-mode project configuration, not by the static bundle.
- Deployed backend preview successfully from `backend/`:
  - Preview: `https://backend-eywrx87ki-d1sneys-projects.vercel.app`
  - Inspect: `https://vercel.com/d1sneys-projects/backend/Caygjo6xntFsiCf7YCweb9HMQuUe`
- Verified backend preview through `vercel curl` because preview deployment protection returns Vercel Authentication HTML to unauthenticated HTTP clients.
- Fixed readiness error wrapping so missing/unreachable production DB returns typed `DATABASE_UNAVAILABLE` instead of a generic 500.
- Created final review and verification artifacts.

## Verification Highlights

| Check | Result |
| --- | --- |
| `node --test tests/phase7-static-contract.test.mjs tests/phase8-deploy-config.test.mjs` | passed |
| `npm run build:frontend` | passed |
| `docker compose config` from `backend/` | passed |
| `python -m pytest` from `backend/` | passed |
| `python -m ruff check .` from `backend/` | passed |
| `python -m ruff format --check .` from `backend/` | passed |
| Local smoke helper against `localhost:3000` and `localhost:8000` | passed with `/ready` skipped |
| Backend Vercel preview deploy | READY |
| Backend preview `/health` via `vercel curl` | passed |
| Backend preview `/ready` without production DB env | expected `DATABASE_UNAVAILABLE` |
| Backend preview OAuth login without provider env | expected `OAUTH_PROVIDER_NOT_CONFIGURED` |

## External Blockers

- Frontend Vercel project `comicly.ai` is linked but currently configured in Services mode. Redeploying root static output fails with `No services configured. Add experimentalServices to vercel.json.` The fix is dashboard-side: recreate or reconfigure the frontend as a standard static Vercel project.
- Production domains `comicly.ai`, `www.comicly.ai`, and `api.comicly.ai` are not bound in this thread.
- Production env values are not configured in this thread: Neon runtime/migration URLs, Vercel Blob token, OAuth client secrets, session/cookie settings, and OpenRouter key.
- Live Google/Yandex OAuth and live OpenRouter generation were not run because production provider secrets/domains are required.

## Self-Check

PASSED WITH EXTERNAL BLOCKERS. Phase 8 code, docs, local gates, and backend preview readiness are complete. Full public production smoke remains blocked by Vercel dashboard project mode, domains, and production secrets.
