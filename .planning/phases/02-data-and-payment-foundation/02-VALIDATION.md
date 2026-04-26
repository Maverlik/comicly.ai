---
phase: 2
slug: data-and-payment-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-26
---

# Phase 2 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Pytest + HTTPX/FastAPI test client + SQLAlchemy/Alembic checks |
| **Config file** | `backend/pytest.ini`, `backend/pyproject.toml` |
| **Quick run command** | `python -m pytest` |
| **Full suite command** | `python -m pytest && python -m ruff check . && python -m ruff format --check .` |
| **Estimated runtime** | ~30-120 seconds without Docker integration; longer when migration tests use Postgres |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest`
- **After every plan wave:** Run `python -m pytest && python -m ruff check . && python -m ruff format --check .`
- **Before `$gsd-verify-work`:** Full suite plus migration verification must be green or clearly environment-blocked.
- **Max feedback latency:** 120 seconds for non-Docker checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | DATA-02, DATA-05 | T-2-CONFIG | Settings separate pooled runtime DB URL from direct migration URL and centralize pricing | unit | `python -m pytest tests/test_config.py` | W0 | pending |
| 2-01-02 | 01 | 1 | DATA-02 | T-2-SCHEMA | Required model metadata exists without creating business behavior | unit | `python -m pytest tests/test_models.py` | W0 | pending |
| 2-02-01 | 02 | 2 | DATA-01, DATA-02 | T-2-MIGRATION | Alembic creates required tables from clean metadata | integration | `python -m alembic upgrade head` | W0 | pending |
| 2-02-02 | 02 | 2 | DATA-03, PAY-02, PAY-03 | T-2-CONSTRAINTS | DB rejects duplicate identities/idempotency and invalid balances | integration/unit | `python -m pytest tests/test_schema_constraints.py` | W0 | pending |
| 2-03-01 | 03 | 3 | DATA-04, DATA-05, PAY-01 | T-2-SEED | Seed/catalog path creates active packages and exposes only safe catalog data | integration | `python -m pytest tests/test_coin_packages.py` | W0 | pending |
| 2-03-02 | 03 | 3 | DATA-01..PAY-03 | - | Docs explain local Docker DB, Neon pooled runtime URL, direct migration URL, and no production Compose | review/command | `python -m pytest && python -m ruff check . && python -m ruff format --check .` | W0 | pending |

*Status: pending, green, red, flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_models.py` - model metadata and table presence.
- [ ] `backend/tests/test_schema_constraints.py` - representative constraints.
- [ ] `backend/tests/test_coin_packages.py` - seed/catalog/pricing behavior.
- [ ] `backend/app/models/` - model modules imported by `Base.metadata`.
- [ ] Alembic migration file under `backend/alembic/versions/`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Production Neon/Vercel env values exist | DATA-01, OPS later | Real production project may not exist during Phase 2 | Verify docs list `DATABASE_URL` pooled runtime URL and direct migration URL; do not require live production deploy in Phase 2. |
| Docker Postgres integration | DATA-01 | Depends on local Docker availability | From `backend/`, run `docker compose up -d`, then run migration verification against local Postgres. |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s for non-Docker checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
