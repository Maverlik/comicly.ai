# Phase 7 Research: Creator Frontend Backend Integration

## Research Complete

### What Matters For Planning

Phase 7 is a brownfield static frontend integration, not a UI rewrite. The current creator is plain HTML/CSS/JS served by the root Node server, with all creator state in `scripts/creator.js`. The backend is a separate FastAPI API with cookie-authenticated v1 routes.

The plan must preserve the existing creator shell while replacing these demo/root behaviors:
- hardcoded `credits = 240`;
- fake profile/logout/add-credits behavior;
- old root AI endpoints `/api/ai-text` and `/api/generate-comic-page`;
- local-only generated page state as the source of truth after generation.

### Existing Frontend Integration Points

- `create.html` already has profile menu, credit balance, generation button, loading state, page strip, scene editor, and toast target.
- `creator.css` already owns creator layout and should receive only scoped state styles for auth overlay, status/error, disabled generation action, and backend save state.
- `scripts/creator.js` already centralizes page/scene state, generation payload creation, loading toggles, toasts, undo/redo, and profile actions.

### Backend API Contracts To Use

- `GET /api/v1/me` returns account/profile/wallet bootstrap data and 401 for unauthenticated users.
- `POST /api/v1/me/logout` revokes the current session and clears the cookie.
- `POST /api/v1/comics` creates the current private comic draft.
- `PATCH /api/v1/comics/{comic_id}` updates metadata.
- `PUT /api/v1/comics/{comic_id}/scenes` replaces scenes.
- `PUT /api/v1/comics/{comic_id}/pages` can persist non-generated page records if needed.
- `POST /api/v1/ai-text` replaces the old root text helper endpoint.
- `POST /api/v1/generations` replaces the old root image endpoint, requires `Idempotency-Key`, and returns job/page/balance/image URL.

### API Base Strategy

Because the current frontend is static and may be served from a different origin than the backend:
- use a small frontend API helper with `credentials: "include"`;
- resolve API base from an optional `window.COMICLY_API_BASE_URL`, then local defaults, then production `https://api.comicly.ai`;
- avoid build-time env requirements for MVP static hosting.

Local default should support:
- frontend/root static server at `http://localhost:3000`;
- FastAPI backend at `http://localhost:8000`.

Production default should support:
- frontend at `comicly.ai` / `www.comicly.ai`;
- backend at `https://api.comicly.ai`.

### Hybrid Save Model

A practical Phase 7 hybrid:
- create a backend comic lazily once an authenticated user starts generation or first meaningful save is needed;
- save metadata/scenes before generation so `POST /api/v1/generations` has a real `comic_id` and optional `scene_id`;
- debounce non-critical metadata/scenes saves where feasible;
- show a small save status/error state, but do not block editing on save except when generation needs a fresh backend comic context.

Full history/reopen UI is deferred, so the frontend does not need to list old comics in Phase 7.

### Verification Architecture

Automated coverage can combine:
- root/static contract tests for public landing and creator auth UI markers;
- backend API tests already covering auth/wallet/comics/generation behavior;
- browser smoke with backend and static site running to verify visible unauth gate and basic authenticated creator behavior.

OAuth provider login cannot be fully automated without live provider credentials. Phase 7 smoke can verify login button targets plus session-check behavior using a seeded/known local session or documented manual OAuth check.

### Key Risks

- Cross-origin cookies fail if frontend fetches omit `credentials: "include"` or CORS env is not configured.
- Frontend may need a current backend comic before generation; plan must ensure `comic_id` exists before calling `/api/v1/generations`.
- Edits during generation must not mutate the in-flight payload; use click-time snapshots.
- `Add credits` must not remain as a fake production action.
- Branch must sync `origin/main` before frontend/root edits, per user requirement.
