---
phase: 1
slug: backend-foundation-and-static-safety
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-26
---

# Phase 1 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Pytest + HTTPX/FastAPI test client |
| **Config file** | `backend/pytest.ini` or `backend/pyproject.toml` if planner chooses one |
| **Quick run command** | `python -m pytest` |
| **Full suite command** | `python -m pytest && python -m ruff check . && python -m ruff format --check .` |
| **Estimated runtime** | ~30-90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest`
- **After every plan wave:** Run `python -m pytest && python -m ruff check . && python -m ruff format --check .`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | SAFE-02 | - | Backend modules import and app starts from `backend/` only | unit/integration | `python -m pytest` | W0 | pending |
| 1-01-02 | 01 | 1 | SAFE-03, SAFE-04 | - | Validation and app errors return stable JSON shape | integration | `python -m pytest` | W0 | pending |
| 1-02-01 | 02 | 2 | OPS-06 | - | `/health` does not expose secrets; `/ready` checks DB without leaking config | integration | `python -m pytest` | W0 | pending |
| 1-02-02 | 02 | 2 | SAFE-01 | T-1-STATIC | API-only backend does not serve private/root/frontend files | integration | `python -m pytest` | W0 | pending |
| 1-03-01 | 03 | 3 | TEST-01 | - | Test/lint/format commands are documented and executable | command | `python -m pytest && python -m ruff check . && python -m ruff format --check .` | W0 | pending |
| 1-03-02 | 03 | 3 | SAFE-05 | - | Existing AI route migration boundary is documented; Phase 1 does not alter frontend/root prototype | review/test | `git diff --name-only` plus plan checklist | W0 | pending |

*Status: pending, green, red, flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` - shared app/settings fixtures.
- [ ] `backend/tests/test_health.py` - `/health` and `/ready` behavior.
- [ ] `backend/tests/test_static_safety.py` - representative private/root/frontend paths are not served.
- [ ] `backend/tests/test_config.py` - config loading and safe defaults.
- [ ] `backend/requirements.txt` - includes Pytest, HTTPX, Ruff, FastAPI, SQLAlchemy, Alembic, asyncpg.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker Compose backend app + Postgres startup | SAFE-02, OPS-06 | Depends on local Docker availability | From `backend/`, run `docker compose up --build`; verify backend starts and `/health` and `/ready` can be requested. |
| No frontend/root files changed | Phase context D-03/D-04 | Git review is clearer than automated test alone | Run `git diff --name-only` and confirm runtime changes are scoped to `backend/`. |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
