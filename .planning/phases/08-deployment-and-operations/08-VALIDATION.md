---
phase: 08
slug: deployment-and-operations
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-29
---

# Phase 08 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
| --- | --- |
| **Backend framework** | pytest + ruff |
| **Backend config** | `backend/pytest.ini`, `backend/pyproject.toml` |
| **Frontend/static framework** | Node built-in test runner |
| **Frontend config** | `tests/phase7-static-contract.test.mjs` |
| **Quick run command** | `cd backend; python -m pytest tests/test_security_middleware.py tests/test_config.py` |
| **Full suite command** | `cd backend; python -m pytest; python -m ruff check .; python -m ruff format --check .` |
| **Estimated runtime** | ~30-90 seconds locally |

## Sampling Rate

- **After every task commit:** Run the quickest relevant test for the touched area.
- **After every plan wave:** Run the full backend suite plus relevant root/static tests.
- **Before `$gsd-verify-work`:** Backend gates, root/static deployment checks, and deployment smoke notes must be green or explicitly blocked by external credentials.
- **Max feedback latency:** 90 seconds for local checks.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 08-01-01 | 01 | 1 | OPS-03, OPS-04 | T-08-01 | Frontend deployment publishes only allow-listed static files | unit/script | `node --test tests/phase8-deploy-config.test.mjs` | yes | pending |
| 08-01-02 | 01 | 1 | OPS-03, OPS-04 | T-08-02 | Backend Vercel config exposes FastAPI without Docker Compose production coupling | manual/unit | `node --test tests/phase8-deploy-config.test.mjs` | yes | pending |
| 08-02-01 | 02 | 2 | OPS-05 | T-08-03 | API responses include production-safe security headers | unit | `cd backend; python -m pytest tests/test_security_middleware.py` | yes | pending |
| 08-02-02 | 02 | 2 | OPS-05 | T-08-04 | Sensitive endpoints are rate limited with stable JSON errors | unit | `cd backend; python -m pytest tests/test_security_middleware.py` | yes | pending |
| 08-03-01 | 03 | 3 | OPS-01, OPS-02, OPS-03 | T-08-05 | Env/docs list required settings without secrets | unit/manual | `node --test tests/phase8-deploy-config.test.mjs` | yes | pending |
| 08-03-02 | 03 | 3 | OPS-04 | T-08-06 | Smoke tooling distinguishes automated checks from provider-secret-dependent manual checks | manual/script | `python backend/scripts/smoke_production.py --base-url http://localhost:8000 --frontend-url http://localhost:3000` | yes | pending |
| 08-04-01 | 04 | 4 | OPS-01..OPS-05 | T-08-07 | Final verification records deployed status or exact external blockers | manual | deployment smoke commands in 08-04 | yes | pending |

## Wave 0 Requirements

Existing infrastructure covers the phase. Plan 01 may add root deployment-config tests, and Plan 02 may add backend security middleware tests.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
| --- | --- | --- | --- |
| Vercel project creation/linking | OPS-04 | Requires authenticated Vercel account/project access | Use Vercel tools/CLI during Plan 04; record project URLs or blocker. |
| DNS/domain binding for `comicly.ai`, `www.comicly.ai`, `api.comicly.ai` | OPS-04 | Requires domain ownership/DNS state | Verify Vercel dashboard/domain status and smoke final URLs. |
| Google/Yandex live OAuth callback | OPS-04 | Requires provider console credentials and registered callbacks | Start login flow from production creator and confirm session returns to `/create.html`. |
| Live OpenRouter generation with Vercel Blob | OPS-04 | Requires production secrets and provider quota | Generate one page and verify response returns Blob `image_url` plus updated balance. |

## Validation Sign-Off

- [x] All plans have automated checks or explicit manual-provider gates.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers existing test infrastructure.
- [x] No watch-mode flags.
- [x] Feedback latency under 90 seconds for local checks.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved 2026-04-29
