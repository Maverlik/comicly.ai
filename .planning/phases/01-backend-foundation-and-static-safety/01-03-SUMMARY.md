---
phase: 01-backend-foundation-and-static-safety
plan: 03
subsystem: testing
tags: [pytest, httpx, ruff, fastapi, static-safety, docs]

requires:
  - phase: 01-01
    provides: FastAPI app factory, Settings, ApiError, and validation error envelope
  - phase: 01-02
    provides: Unprefixed /health and /ready routes plus database readiness helper
provides:
  - Pytest fixtures and API tests for health, readiness, config, errors, validation, and static safety
  - Ruff lint and format configuration for Python 3.12 backend code
  - Backend README with local, Docker, test, lint, format, migration, env, and scope commands
  - Phase 1 boundary documentation preserving root Node AI route ownership
affects: [phase-2-data-model, backend-quality-gates, static-safety, migration-boundary]

tech-stack:
  added: []
  patterns: [httpx-asgi-tests, monkeypatched-readiness-checks, api-only-static-safety-tests, backend-scope-docs]

key-files:
  created:
    - backend/tests/conftest.py
    - backend/tests/test_health.py
    - backend/tests/test_config.py
    - backend/tests/test_errors.py
    - backend/tests/test_static_safety.py
    - backend/pytest.ini
    - backend/pyproject.toml
    - backend/README.md
    - backend/docs/phase1-boundary.md
  modified: []

key-decisions:
  - "Use HTTPX ASGITransport fixtures against create_app() for backend-only API tests."
  - "Treat Phase 1 static safety as an API-only negative guarantee: no StaticFiles mount and representative private/root/frontend paths are not served."
  - "Preserve existing root Node AI route ownership and document FastAPI migration as a later approved plan."

patterns-established:
  - "Readiness tests monkeypatch app.api.health.check_database_ready so unit-like API tests do not require Docker Postgres."
  - "Static safety tests assert the FastAPI backend is not a repository-root or frontend file server."
  - "Backend quality commands are documented as python -m pytest, python -m ruff check ., and python -m ruff format --check . from backend/."

requirements-completed: [SAFE-01, SAFE-03, SAFE-04, SAFE-05, OPS-06, TEST-01]

duration: 6min
completed: 2026-04-26
---

# Phase 1 Plan 03: Quality Gates, Static Safety, And Documentation Summary

**Pytest/Ruff safety net proving the FastAPI backend is API-only while documenting the root Node AI route migration boundary**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-26T08:08:30Z
- **Completed:** 2026-04-26T08:14:25Z
- **Tasks:** 3
- **Files modified:** 9 backend files plus this summary and state documents

## Accomplishments

- Added HTTPX/ASGI pytest coverage for `/health`, `/ready`, config safe defaults, stable API error envelopes, and validation errors.
- Added static safety tests proving representative private, root, frontend, dotfile, backend-doc, and traversal paths are not served by the FastAPI backend.
- Added Ruff lint/format configuration and backend README commands for local setup, Docker Compose, tests, lint, format, Alembic, env variables, and root-change guard checks.
- Added Phase 1 boundary docs stating the existing root Node runtime still owns `/api/health`, `/api/ai-text`, and `/api/generate-comic-page` until a later approved migration.

## Task Commits

Plan implementation was committed atomically per the execution request:

1. **Tasks 1-3: Backend safety tests, Ruff config, README, and boundary docs** - `e16a862` (test)

## Files Created/Modified

- `backend/tests/conftest.py` - Shared async HTTPX ASGI client fixture against `create_app()`.
- `backend/tests/test_health.py` - `/health` non-secret payload tests and `/ready` success/failure tests with controlled readiness overrides.
- `backend/tests/test_config.py` - Settings tests proving future OAuth/OpenRouter/wallet/payment env vars are not required for Phase 1 startup.
- `backend/tests/test_errors.py` - Stable machine-readable error envelope and validation response tests.
- `backend/tests/test_static_safety.py` - Representative private/root/frontend/traversal denial tests and no-`StaticFiles` assertion.
- `backend/pytest.ini` - Pytest backend pythonpath, async mode, and test discovery config.
- `backend/pyproject.toml` - Ruff Python 3.12 lint/format config.
- `backend/README.md` - Backend setup, Docker, quality gate, migration, env, and scope-boundary commands.
- `backend/docs/phase1-boundary.md` - Phase 1 backend-only and AI route migration boundary.

## Decisions Made

- Kept readiness tests unit-like by monkeypatching the imported readiness helper in `app.api.health`, avoiding a Docker Postgres dependency for the planned API contract tests.
- Configured Ruff with focused baseline rules (`E`, `F`, `I`, `UP`, `B`) plus a FastAPI `Query` allowance for validation test routes.
- Documented existing root AI routes as preserved by non-modification rather than reimplementing or importing root `server.js`.

## Deviations from Plan

### Auto-fixed Issues

None - implementation scope followed the plan.

### Execution Adjustments

- Used one atomic implementation commit instead of separate TDD red/green commits because the user execution rules explicitly requested atomic plan completion, matching Plans 01 and 02.
- Added Ruff Bugbear config for `fastapi.Query` so the selected lint rules are compatible with FastAPI validation test route patterns.

## Issues Encountered

- `python` resolves to `C:\Users\ivan3\AppData\Local\Microsoft\WindowsApps\python.exe`, which fails with "Access to this file from the system is unavailable."
- `python3` resolves to the same unavailable Windows Store shim, and `py` is not installed.
- `python -m pytest`, `python -m ruff check .`, and `python -m ruff format --check .` could not run in this environment because Python fails before loading pytest or Ruff.
- The PowerShell `gsd-sdk` shim is blocked by execution policy, and `gsd-sdk.cmd` does not expose the documented `query` handlers. State, roadmap, and requirements updates were applied manually.

## Verification

Source-level checks completed:

- Confirmed `backend/pytest.ini` sets `pythonpath = .`, `asyncio_mode = auto`, and `testpaths = tests`.
- Confirmed `backend/pyproject.toml` targets Python 3.12 and configures Ruff lint/format checks.
- Confirmed `backend/tests/test_static_safety.py` covers `.env`, `.planning/PROJECT.md`, `backend/BACKEND_TZ.md`, `package.json`, frontend files, and traversal paths.
- Confirmed `backend/README.md` documents `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .`, Uvicorn, Docker Compose, Alembic, `/api/v1/`, env variables, and the root-change guard.
- Confirmed `backend/docs/phase1-boundary.md` documents root Node ownership of `GET /api/health`, `POST /api/ai-text`, and `POST /api/generate-comic-page`.
- Confirmed the root-change guard command produced no output.
- Confirmed implementation commit `e16a862` deleted no tracked files.

Blocked by local environment:

- `cd backend; python -m pytest tests/test_health.py tests/test_config.py tests/test_errors.py`
- `cd backend; python -m pytest tests/test_static_safety.py`
- `cd backend; python -m pytest`
- `cd backend; python -m ruff check .`
- `cd backend; python -m ruff format --check .`

## Known Stubs

None.

## Threat Flags

None - Plan 03 introduced only tests and documentation for the threat surfaces identified in the plan threat model.

## Auth Gates

None.

## User Setup Required

Install or enable Python 3.12 locally, then run the backend quality gates from `backend/`:

```powershell
python -m pip install -r requirements.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Next Phase Readiness

Phase 1 now has the backend app scaffold, health/readiness routes, DB/Alembic foundation, API error contract, static-safety coverage, Ruff config, and backend docs needed before Phase 2 adds durable data models and payment-ready schema.

## Self-Check: PASSED

- Required created files exist.
- Implementation commit `e16a862` is visible in git history.
- No tracked files were deleted by the implementation commit.
- `backend/BACKEND_TZ.md` remained untracked and untouched.

---
*Phase: 01-backend-foundation-and-static-safety*
*Completed: 2026-04-26*
