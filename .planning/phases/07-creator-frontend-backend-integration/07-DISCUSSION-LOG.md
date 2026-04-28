# Phase 7: Creator Frontend Backend Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 7 - Creator Frontend Backend Integration
**Areas discussed:** Auth Entry, Initial Creator State, Save Model, Comic History UI, Generation UX, Legacy Demo State, Verification Scope, Main Sync Before Frontend Edits

---

## Auth Entry

| Option | Description | Selected |
| --- | --- | --- |
| Soft login overlay | Creator shows an explanatory login screen with OAuth buttons | yes |
| Automatic OAuth redirect | Creator immediately redirects to OAuth | no |
| Demo/read-only mode | Unauthenticated users can use demo creator | no |

**User's choice:** Soft login overlay on creator only.
**Notes:** Landing page remains public and must not auto-redirect.

---

## Initial Creator State

| Option | Description | Selected |
| --- | --- | --- |
| Empty new creator | Start from a blank new creator state after login | yes |
| Last comic | Auto-open most recent comic | no |
| Comic list first | Show history/list before workspace | no |

**User's choice:** Empty new creator state.
**Notes:** Backend history can remain available, but frontend does not show it in Phase 7.

---

## Save Model

| Option | Description | Selected |
| --- | --- | --- |
| Hybrid | Combine responsive local editing with server persistence/status | yes |
| Manual only | Save only on explicit action | no |
| Aggressive autosave only | Save every edit automatically | no |

**User's choice:** Hybrid.
**Notes:** Exact save triggers are left to planning/implementation.

---

## Comic History UI

| Option | Description | Selected |
| --- | --- | --- |
| No history UI | Current result only; history deferred | yes |
| Drawer/modal list | Add lightweight old-comics picker | no |
| Full history workflow | Reopen/list/archive UI | no |

**User's choice:** No comic history UI in Phase 7.
**Notes:** History, reopen, drafts, archive/list/detail UI are future features.

---

## Generation UX

| Option | Description | Selected |
| --- | --- | --- |
| Block generation action only | Disable only the active generation action | yes |
| Block entire workspace | Lock all editing until generation finishes | no |
| Background only | Let generation run without clear loading | no |

**User's choice:** Block only generation button/action with clear loading text.
**Notes:** In-flight request uses payload snapshot from click time; later edits must not mutate that request.

---

## Legacy Demo State

| Option | Description | Selected |
| --- | --- | --- |
| Strict backend truth | Replace fake profile/credits/add credits/demo truth | yes |
| Local demo fallback | Keep fake data when backend unavailable | no |
| Mixed mode | Backend when available, demo otherwise | no |

**User's choice:** Strict backend truth.
**Notes:** Backend unavailable should show a clean error state, not fake production data.

---

## Verification Scope

| Scenario | Required |
| --- | --- |
| Unauthenticated user sees login screen | yes |
| Login/session check | yes |
| Profile/balance load from backend | yes |
| Creator sends generation request | yes |
| Generation loading state | yes |
| Success image/result and updated balance | yes |
| Insufficient coins error | yes |
| Failed generation error | yes |
| Logout | yes |
| Landing remains public | yes |

**User's choice:** All listed scenarios are required smoke coverage.

---

## Main Sync Before Frontend Edits

| Requirement | Selected |
| --- | --- |
| Check git status first | yes |
| Preserve current backend/planning work | yes |
| Fetch/pull `origin/main` | yes |
| Merge/rebase main into current branch | yes |
| Resolve conflicts before frontend edits | yes |

**User's choice:** Mandatory before Phase 7 frontend/root/static creator changes.

---

## Deferred Ideas

- Comic history UI, reopen existing comic, drafts, archive/list/detail frontend.
- Demo/read-only mode.
- Payment/add credits UI.
- Frontend framework migration.
