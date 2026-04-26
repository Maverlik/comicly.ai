# Phase 1: Backend Foundation And Static Safety - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `01-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-04-26
**Phase:** 1 - Backend Foundation And Static Safety
**Areas discussed:** backend boundary, stack, dependency tooling, Docker scope, health/readiness, API prefix

---

## Backend Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Backend only inside `backend/` | Implement backend as a standalone entity in `backend/`; do not modify frontend/root without separate approval. | yes |
| Full repo migration | Update root server/frontend wiring as part of Phase 1. | no |

**User's choice:** Backend must be implemented only inside `backend/`; frontend and other project areas require separate confirmation.
**Notes:** `backend/BACKEND_TZ.md` is the source of truth for backend requirements.

---

## Stack

| Option | Description | Selected |
|--------|-------------|----------|
| Node.js + TypeScript + Express + PostgreSQL + Drizzle | Closer to current Node prototype, but less familiar to user. | no |
| Node.js + TypeScript + NestJS + PostgreSQL + Prisma | More structured, heavier framework. | no |
| Python + FastAPI + PostgreSQL + SQLAlchemy/Alembic | Independent backend stack the user knows better; OpenRouter logic will be rewritten anyway. | yes |

**User's choice:** Python + FastAPI + PostgreSQL + SQLAlchemy/Alembic.
**Notes:** Python 3.12 selected as the conservative stable runtime.

---

## Dependency Tooling

| Option | Description | Selected |
|--------|-------------|----------|
| `uv` | Faster and modern Python tooling. | no |
| Poetry | More managed project/dependency workflow. | no |
| `pip + requirements.txt` | Simple, standard setup for MVP. | yes |

**User's choice:** `pip + requirements.txt`.
**Notes:** Simplicity and easy maintenance are preferred for MVP.

---

## Docker Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Postgres only | Compose starts only database; app runs locally. | no |
| Backend app + Postgres | Compose starts standalone API container and database. | yes |

**User's choice:** Include both backend app and PostgreSQL in Phase 1 Docker setup.
**Notes:** This matches future expectation that backend may run separately or in a neighboring container.

---

## Health And Readiness

| Option | Description | Selected |
|--------|-------------|----------|
| `/health` only | Single lightweight health endpoint. | no |
| `/health` and `/ready` | App health plus dependency readiness checks. | yes |

**User's choice:** Add both `GET /health` and `GET /ready`.
**Notes:** `/ready` should check database connectivity once DB wiring exists.

---

## API Prefix

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix everything under `/api/v1` | Even health endpoints are versioned. | no |
| Unprefixed health, business routes under `/api/v1` | `/health` and `/ready`; future business APIs under `/api/v1/...`. | yes |

**User's choice:** Keep health endpoints unprefixed; future business routes use `/api/v1/...`.

---

## the agent's Discretion

- Exact backend package/module naming.
- Exact health response JSON shape.
- Exact Docker service names and local ports, subject to documentation and avoiding unnecessary conflicts.

## Deferred Ideas

- Business feature implementation from `backend/BACKEND_TZ.md` is deferred to later phases.
- Frontend integration is deferred and requires separate confirmation before touching frontend files.
