---
phase: 08-deployment-and-operations
type: verification
status: complete-with-external-blockers
verified_at: 2026-04-29
---

# Phase 8 Verification

## Verdict

Phase 8 is implementation-complete. Local quality gates pass, backend preview deploys on Vercel, and a corrected static frontend project now deploys on Vercel. Public production-live checks remain blocked by domain and secret setup.

## Requirement Mapping

| Requirement | Status | Evidence |
| --- | --- | --- |
| OPS-01 `.env.example` coverage | Pass | Root and backend env examples document local/static and production backend variables without real secrets. |
| OPS-02 local setup instructions | Pass | `backend/README.md` and `backend/docs/deployment.md` cover install, Docker Postgres, migrations, tests, and server startup. |
| OPS-03 production deployment instructions | Pass | `backend/docs/deployment.md` covers Vercel projects, Neon pooled/direct URLs, Blob, OAuth callbacks, cookies, env, smoke, fallback, and rollback. |
| OPS-04 production deployment | Partial/external | Backend preview deploy is READY and smokeable via `vercel curl`; corrected frontend project `comicly-frontend` deploys to Vercel; production domains, DB/storage, OAuth secrets, and live generation are not configured in this thread. |
| OPS-05 security headers and rate limits | Pass | Middleware implemented, tested, and enabled by default with env toggles. |

## Commands Run

From repository root:

```powershell
node --test tests/phase7-static-contract.test.mjs tests/phase8-deploy-config.test.mjs
npm run build:frontend
```

From `backend/`:

```powershell
docker compose config
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Smoke and deploy checks:

```powershell
python backend/scripts/smoke_production.py --api-base-url http://localhost:8000 --frontend-url http://localhost:3000 --skip-ready
npx vercel whoami
npx vercel project ls
npx vercel deploy --yes --no-color
npx vercel curl /health --deployment backend-eywrx87ki-d1sneys-projects.vercel.app --no-color
npx vercel curl /ready --deployment backend-eywrx87ki-d1sneys-projects.vercel.app --no-color
npx vercel curl /api/v1/auth/google/login --deployment backend-eywrx87ki-d1sneys-projects.vercel.app --no-color
npx vercel project add comicly-frontend
npx vercel link --yes --project comicly-frontend --team team_ticMiLg5X6NzXzK0jGi2fvaV --no-color
npx vercel deploy --yes --no-color
curl.exe -L -I https://comicly-frontend.vercel.app/
curl.exe -L -I https://comicly-frontend.vercel.app/create.html
```

## Deploy Results

| Target | Result |
| --- | --- |
| Vercel CLI auth | Passed as `d1sney` |
| Backend Vercel preview | READY: `https://backend-eywrx87ki-d1sneys-projects.vercel.app` |
| Backend preview `/health` | Passed: `{"status":"ok"}` |
| Backend preview `/ready` before Neon env | Expected: `DATABASE_UNAVAILABLE` |
| Backend preview OAuth before provider env | Expected: `OAUTH_PROVIDER_NOT_CONFIGURED` |
| Old root frontend Vercel project `comicly.ai` | Blocked by Services-mode config: `No services configured. Add experimentalServices to vercel.json.` |
| Corrected frontend Vercel project `comicly-frontend` | READY: `https://comicly-frontend.vercel.app` |
| Corrected frontend `/` | Passed: HTTP 200 |
| Corrected frontend `/create.html` | Passed after Vercel clean URL redirect to `/create`: HTTP 308 then HTTP 200 |

## Unrun Live Checks

- Public `https://comicly.ai` and `https://api.comicly.ai` smoke checks were not run because production domains are not attached to the corrected frontend/backend projects yet.
- Live Google/Yandex OAuth was not run because provider credentials and production callback domains are not configured.
- Live OpenRouter generation and Vercel Blob persistence were not run because production secrets/storage and authenticated test user setup are required.

## Conclusion

Phase 8 can be closed for application implementation. Frontend static Vercel deployment now works through `comicly-frontend`. Public production launch still needs Vercel dashboard work: domain attachment, backend env, Neon, Blob, OAuth callbacks, and a final live smoke.
