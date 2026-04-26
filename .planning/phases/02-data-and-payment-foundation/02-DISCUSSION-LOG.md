# Phase 2: Data And Payment Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-26
**Phase:** 02-data-and-payment-foundation
**Areas discussed:** Deployment target, database hosting, generation job shape, roadmap handling, cost constraints

---

## Deployment Target

| Option | Description | Selected |
|--------|-------------|----------|
| Separate Vercel backend project | Deploy `backend/` as its own FastAPI API project on Vercel | yes |
| Vercel Services | Use multi-service Vercel project if stable/available | no |
| Non-Vercel fallback | Render/Railway/Fly if Vercel blocks MVP needs | fallback only |

**User's choice:** Choose the option Codex can most independently configure. If Vercel Services is Private Beta or unstable, use a separate Vercel project from `backend/`.
**Notes:** Frontend should deploy to `comicly.ai` / `www.comicly.ai`; backend API should use `api.comicly.ai`.

---

## Database Hosting

| Option | Description | Selected |
|--------|-------------|----------|
| Neon pooled runtime URL | Use Neon/Vercel Marketplace Postgres with pooled runtime connection | yes |
| Direct migration URL | Use separate direct URL for Alembic migrations if needed | yes |
| Docker Postgres in production | Use Compose/Postgres as production deployment | no |

**User's choice:** `DATABASE_URL` should be the pooled Neon URL for runtime. Add a separate direct migration URL if that is the right FastAPI + SQLAlchemy + Alembic + Neon pattern.
**Notes:** Local DB remains PostgreSQL in `backend/docker-compose.yml`.

---

## Generation Pipeline

| Option | Description | Selected |
|--------|-------------|----------|
| Synchronous MVP | Backend calls OpenRouter/model API directly within Vercel Hobby limits | yes |
| Job-ready schema | Add `generation_jobs` to support later queue/status polling | yes |
| Full queue now | Build enterprise-style async worker pipeline immediately | no |

**User's choice:** Keep MVP simple and synchronous, but design DB structures so a later job/status/queue path does not require rewriting business data models.
**Notes:** This informs Phase 2 schema only; OpenRouter execution stays later.

---

## Roadmap Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Use existing Phase 8 | Keep deployment implementation in current Deployment And Operations phase | yes |
| Add Phase 2.1 | Insert early Vercel/Neon deployment spike | optional later |

**User's choice:** Not especially important; do not add extra phase by default.
**Notes:** Context captures that Phase 2 should be deployment-compatible, not that Phase 2 executes deployment.

---

## Cost Constraints

| Option | Description | Selected |
|--------|-------------|----------|
| Budget/token-efficient mode | Avoid unnecessary subagents and deep research | yes |
| Deep research now | Broadly investigate every hosting alternative | no |

**User's choice:** Work in budget/token-efficient mode. Use official docs briefly; do not run multi-agent or deep research without explaining why first.
**Notes:** Vercel-first remains preferred unless critical limitations appear.

---

## the agent's Discretion

- Pick exact direct migration URL env var name during planning.
- Decide the simplest seed mechanism for coin packages.
- Decide exact SQLAlchemy model/table naming.

## Deferred Ideas

- Early Phase 2.1 Vercel/Neon smoke deploy, only if the user later wants it.
- Non-Vercel backend fallback, only if Vercel limitations block MVP.
