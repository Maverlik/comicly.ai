# Phase 7 UI Spec: Creator Backend Integration

## Status

Approved for planning.

## Product Intent

The creator should feel like the same Comicly.ai workspace, but with real account and wallet state. Phase 7 should not introduce a dashboard or history view. The work is a trust upgrade: account-required creator, backend balance, backend generation, durable result, and clear failures.

## Scope

In scope:
- creator-only unauthenticated overlay;
- account/profile/balance display from backend;
- backend unavailable/auth/session states;
- generation loading/success/error states;
- logout state transition;
- small save status if needed by hybrid save.

Out of scope:
- landing page auth treatment;
- comic history/list/reopen UI;
- payment/add credits purchase UI;
- full redesign or framework migration.

## Visual Contract

### Auth Overlay
- The overlay appears only on `create.html`.
- It should sit above the creator shell and prevent editing until authenticated.
- Copy: "Войдите, чтобы создавать комиксы".
- Include two clear OAuth buttons: Google and Yandex.
- Use the current creator visual language: dark workspace, restrained panel surface, existing button styles where possible.
- Do not use marketing hero composition or a new landing-style layout.

### Authenticated Empty State
- After session check passes, the creator opens as a blank/new comic workspace.
- Do not show a comic history sidebar, modal, or list.
- Existing placeholder pages are acceptable only as visual empty placeholders; they must not represent trusted generated/history data.

### Profile And Balance
- Profile display must use backend account data from `/api/v1/me`.
- Balance display must use backend wallet balance.
- Fake add-credits behavior must not look actionable in production. Remove, disable, hide, or convert it to a future/payment unavailable state.

### Loading And Error States
- Generation loading text should be explicit: "Генерируем страницу/изображение...".
- Only the active generation action is disabled during generation; the workspace remains editable.
- Backend unavailable/auth failures should show calm, user-readable messages with no debug dumps.
- Insufficient coins and generation failures should be shown as normal recoverable errors.

### Save State
- If save status is visible, use compact copy such as "Сохранено", "Сохраняем...", or "Не удалось сохранить".
- Save status must not dominate the creator.

## Interaction Contract

- On creator load, call session/bootstrap API and show either auth overlay or creator.
- Login buttons navigate to backend OAuth routes.
- Logout calls backend logout, then returns creator to the auth overlay.
- Generation captures a payload snapshot at click time.
- Later edits during generation affect future requests only.
- Generation success updates the visible image and wallet balance from backend response.
- AI text helper actions call backend `/api/v1/ai-text`.

## Responsive Contract

- Existing desktop and mobile creator layout should remain intact.
- Auth overlay, loading, and errors must fit mobile without text overflow.
- New controls should reuse existing button/input scale and avoid large new panels inside panels.

## Verification Contract

Screens/smokes must confirm:
- landing remains public;
- unauthenticated creator shows login overlay;
- authenticated creator shows profile/balance from backend;
- generation loading disables only the action;
- success displays image/result and updated balance;
- insufficient coins and failed generation show normal messages;
- logout returns to unauthenticated overlay.
