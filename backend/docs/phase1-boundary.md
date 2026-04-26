# Phase 1 Backend Boundary

Phase 1 creates a standalone FastAPI backend under `backend/`. It is API-only and does not serve repository-root files, frontend files, package metadata, planning files, backend documentation, dotfiles, or traversal paths.

The existing root Node runtime remains the owner of the current creator-facing AI contracts during Phase 1:

- `GET /api/health`
- `POST /api/ai-text`
- `POST /api/generate-comic-page`

Those routes are preserved by leaving `server.js`, root package files, and frontend assets untouched. The new FastAPI backend exposes only operational endpoints for this phase: `GET /health` and `GET /ready`.

Future business routes for the FastAPI backend should live under `/api/v1/`. Migrating OpenRouter generation, AI text generation, or frontend calls to FastAPI requires a later approved plan that explicitly allows root/frontend runtime changes and updates the route ownership contract.

This boundary keeps Phase 1 focused on safe extension points: app factory wiring, config defaults, stable error envelopes, database readiness, Alembic setup, tests, and quality gates.
