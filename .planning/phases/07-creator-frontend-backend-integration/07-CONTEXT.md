# Phase 7: Creator Frontend Backend Integration - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 connects the existing static `create.html` creator experience to the authenticated backend truth created in Phases 3-6.

In scope: creator-only auth gate, loading current account/profile/wallet from backend, creating/saving the current comic draft enough to support generation, sending generation and AI text requests to FastAPI v1 APIs, showing durable generation results, updating balance from backend responses, normal error states, and logout.

Out of scope: landing page auth changes, automatic OAuth redirect on landing, read-only demo mode, full comic history UI, reopen/list/archive UI, payment checkout, public gallery/sharing, frontend framework migration, and a broad visual redesign.

</domain>

<decisions>
## Implementation Decisions

### Auth Entry
- **D-01:** The landing page remains public and must not auto-redirect to OAuth.
- **D-02:** On `create.html`, unauthenticated users see a soft screen/overlay with copy like "Войдите, чтобы создавать комиксы" and Google/Yandex login buttons.
- **D-03:** Do not automatically redirect the user immediately when opening the creator; the user should understand why login is needed.
- **D-04:** No demo/read-only creator mode for MVP.

### Initial Creator State
- **D-05:** After login/session validation, show an empty new creator state.
- **D-06:** Do not auto-open the last comic.
- **D-07:** Do not show a comic list/history/recent-comics UI in Phase 7.
- **D-08:** Backend comic history/list/detail APIs remain available, but the frontend should not surface that history yet.

### Save Model
- **D-09:** Use a hybrid save model.
- **D-10:** Frontend should keep creator interactions responsive while persisting meaningful backend state for the current comic/page flow.
- **D-11:** Planning should define the exact save triggers, but the UX should communicate save/error state clearly enough that the user knows whether the current work is backed by the server.

### Comic History UI
- **D-12:** Do not implement a full history UI, drawer, modal, archive UI, or reopen-existing-comic flow in Phase 7.
- **D-13:** The visible creator can focus on the current in-progress result and generated page on screen.
- **D-14:** History, reopen existing comic, drafts list, archive/list/detail UI are future features.

### Generation UX
- **D-15:** During generation, block only the generation button and the specific generation action.
- **D-16:** Do not block the entire workspace while generation is running.
- **D-17:** Show an explicit loading state such as "Генерируем страницу/изображение...".
- **D-18:** If the user edits fields during generation, the active request must still use the snapshot payload from the moment they clicked Generate.

### Backend Truth And Demo State
- **D-19:** Use strict backend truth in production.
- **D-20:** Remove or replace fake credits, fake profile, add-credits behavior, and local demo truth from the production creator flow.
- **D-21:** If the backend is unavailable, show a clear, calm error state rather than falling back to fake production data.
- **D-22:** Frontend endpoints that still call old root AI routes must be replaced with current FastAPI backend API endpoints.

### Required Sync With Main Before Frontend Edits
- **D-23:** Before any Phase 7 frontend/root/static creator file changes, execution must safely update the current branch from `origin/main`.
- **D-24:** Required pre-edit sequence: check `git status`; preserve current backend/planning changes; fetch/pull `origin/main`; merge or rebase main into the current branch; resolve conflicts; only then edit frontend/root/static creator files.
- **D-25:** If conflicts occur during main sync, the executor should resolve them without losing current backend or planning work.

### Verification Scope
- **D-26:** Required smoke checks for Phase 7:
  - unauthenticated user sees login screen on creator;
  - login flow/session check works;
  - profile and balance load from backend;
  - creator sends generation request to FastAPI backend;
  - generation loading state works;
  - successful generation shows image/result and updated balance;
  - insufficient coins error shows a normal message;
  - failed generation shows a normal error and does not break UI;
  - logout works.
- **D-27:** Landing page must remain public and unaffected by the creator auth gate.

### the agent's Discretion
- Exact implementation of hybrid save triggers, as long as current generation flow has the required backend identifiers and UX gives clear save/error feedback.
- Exact visual treatment of the login overlay, as long as it is consistent with the existing creator design and includes Google/Yandex login buttons.
- Exact frontend module/function structure, as long as it stays compatible with the current static HTML/CSS/JS architecture and avoids framework migration.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Scope
- `.planning/PROJECT.md` - project constraints, brownfield/static frontend shape, backend truth principles.
- `.planning/ROADMAP.md` - Phase 7 goal and success criteria.
- `.planning/REQUIREMENTS.md` - `PROF-04` and `TEST-06` requirements.
- `.planning/STATE.md` - current phase position and continuity notes.
- `backend/BACKEND_TZ.md` - backend source-of-truth specification and API expectations.

### Prior Phase Decisions
- `.planning/phases/03-oauth-sessions-and-profile-bootstrap/03-CONTEXT.md` - OAuth redirect/session decisions, login redirect target, 30-day session.
- `.planning/phases/04-wallet-ledger-and-coin-safety/04-CONTEXT.md` - backend-authoritative wallet and idempotency policy.
- `.planning/phases/05-private-comic-persistence/05-CONTEXT.md` - private comic persistence and owner-scoped APIs.
- `.planning/phases/06-production-ai-generation-pipeline/06-CONTEXT.md` - generation API contract, synchronous MVP, Blob storage, idempotency, model policy, and AI text route decisions.
- `.planning/phases/06-production-ai-generation-pipeline/06-VERIFICATION.md` - verified FastAPI generation/text behavior and quality gates.

### Frontend Files
- `create.html` - creator page structure, profile menu, toolbar, scene/page controls, generation button, loading state, and existing public/static markup.
- `creator.css` - creator visual system and states to preserve when adding auth/loading/error UI.
- `scripts/creator.js` - current creator state, demo credits/profile behavior, root AI calls, page/scene rendering, generation flow, toasts, and logout placeholder.

### Backend API Surfaces
- `backend/app/api/v1/me.py` - `GET /api/v1/me`, `PATCH /api/v1/me`, `POST /api/v1/me/logout`.
- `backend/app/api/v1/wallet.py` - `GET /api/v1/wallet`.
- `backend/app/api/v1/comics.py` - private comic create/list/detail/update/scenes/pages APIs.
- `backend/app/api/v1/generations.py` - `POST /api/v1/generations` response and idempotency contract.
- `backend/app/api/v1/ai_text.py` - `POST /api/v1/ai-text` text assistance contract.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/creator.js` already has centralized page/scenes arrays, active page/scene state, generation loading state, toast feedback, page strip rendering, scene editing, and profile menu hooks.
- `create.html` already has a profile menu, credit balance area, generation button, loading overlay, page strip, scene controls, and static creator shell.
- `backend/app/api/v1/me.py` can bootstrap authenticated profile/account/wallet data.
- `backend/app/api/v1/generations.py` returns job/page/balance/image URL for generation.
- `backend/app/api/v1/comics.py` provides the minimal persistence APIs needed to create a current comic and store scenes/pages, even though history UI is deferred.

### Established Patterns
- Frontend is plain static HTML/CSS/JS with no build step; Phase 7 should preserve that.
- Backend private APIs rely on the `comicly_session` cookie and stable JSON error envelope.
- Existing frontend uses toasts for user-visible feedback; new auth/error/generation failures should reuse that style where practical.
- Existing root Node `/api/ai-text` and `/api/generate-comic-page` are migration targets; Phase 7 should switch creator calls to FastAPI v1 APIs.

### Integration Points
- Creator startup should call `GET /api/v1/me` or equivalent session bootstrap to decide whether to show the login overlay or creator.
- Login buttons should link to backend OAuth login routes.
- Logout should call `POST /api/v1/me/logout` and return the creator to the unauthenticated login overlay.
- Generation should ensure there is a current backend comic/page context, send `POST /api/v1/generations` with `Idempotency-Key`, then update image and balance from the response.
- AI text helper actions should call `POST /api/v1/ai-text`.

</code_context>

<specifics>
## Specific Ideas

- Login overlay copy should be direct and product-like: "Войдите, чтобы создавать комиксы".
- Login options should include Google and Yandex.
- Initial post-login state should feel like a blank new comic, not a history/dashboard page.
- Generation must use a snapshot payload captured at button click.
- User can keep editing while generation runs; those edits affect future actions, not the in-flight request.
- Error states should be calm and normal, not debug-like.

</specifics>

<deferred>
## Deferred Ideas

- Comic history UI, recent comics, drafts list, reopen existing comic, archive/list/detail UI.
- Demo/read-only creator mode.
- Payment/add credits UI backed by real checkout.
- Public landing page auth redirect.
- Frontend framework migration.
- Public gallery/sharing/collaboration/admin features.

</deferred>

---

*Phase: 07-creator-frontend-backend-integration*
*Context gathered: 2026-04-28*
