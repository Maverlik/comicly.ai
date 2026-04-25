# Feature Landscape: Comicly.ai Production Backend

**Domain:** AI comic creator production backend
**Researched:** 2026-04-25
**Scope Question:** What v1 feature categories and user capabilities should be scoped for this production backend milestone, based on the current creator UI and backend spec?
**Overall confidence:** HIGH for backend v1 scope from project/spec/codebase docs; MEDIUM for exact API boundaries because implementation planning is still pending.

## Scope Recommendation

The v1 backend milestone should make the existing creator trustworthy and durable without changing the product shape. The current UI already exposes a signed-in account area, coin balance, story/project editor, scene editor, model selector, page generation, scene regeneration, download/share actions, and config feedback. The backend work should convert those visible demo capabilities into server-backed user capabilities.

The core v1 promise is: a user signs in, sees their real profile and coin balance, spends server-accounted coins on AI generation, and can return later to private saved comics and pages. This follows the stated project goal and core value in `.planning/PROJECT.md:7` and `.planning/PROJECT.md:11`, and fixes the current client-only state called out in `.planning/codebase/ARCHITECTURE.md:13` and `.planning/codebase/CONCERNS.md:13`.

## Table Stakes

Missing any item in this section would make the production backend milestone incomplete or leave the current creator behavior materially untrustworthy.

| Feature Category | User Capability | Why v1 | Acceptance Implications | Sources |
|---|---|---|---|---|
| OAuth account access | Sign in with Google or Yandex, return with an existing account, and log out. | The milestone explicitly requires Google/Yandex auth and secure sessions; the UI already has profile/logout affordances. | Google and Yandex login work on production domain; first login creates user/provider identity/profile/wallet; logout invalidates session; private APIs reject anonymous requests. | `.planning/PROJECT.md:27`, `.planning/PROJECT.md:60`, `create.html:52`, `create.html:54`, `.planning/codebase/ARCHITECTURE.md:208` |
| Authenticated creator bootstrap | Open `create.html` and see real account, profile, and wallet state instead of demo data. | The current top bar shows a credit pill and demo profile, but `scripts/creator.js` stores `credits = 240` in memory. | Frontend loads `/api/me` or equivalent; balance and profile are sourced from backend; no trusted balance or user id is accepted from browser input. | `.planning/PROJECT.md:31`, `create.html:40`, `scripts/creator.js:73`, `.planning/codebase/CONCERNS.md:19` |
| Server-side wallet and transaction ledger | See current coin balance and spend coins on generation. | Coin accounting is the backend's source of trust for a paid AI product. | Balance is stored in DB; every debit/credit writes a transaction row; insufficient balance blocks generation with a clear error; balance matches transaction history. | `.planning/PROJECT.md:28`, `.planning/PROJECT.md:29`, `.planning/PROJECT.md:59`, `.planning/codebase/CONCERNS.md:19` |
| Idempotent generation debit | Generate a full comic page for 20 coins without double charges from retries or double-clicks. | Current generation spends OpenRouter credits without auth and subtracts UI credits after success only in the browser. | Backend checks session, validates payload, checks balance, performs generation/persistence/debit in a safe flow, and returns updated balance; duplicate idempotency key does not double debit. | `create.html:247`, `scripts/creator.js:578`, `scripts/creator.js:613`, `.planning/PROJECT.md:59`, `.planning/PROJECT.md:72` |
| Scene regeneration debit | Regenerate the selected scene/page context for 4 coins. | The UI exposes scene regeneration with a 4-credit cost, and the project constraints define that price. | Scene regeneration calls the same protected generation pipeline with a `scene_regeneration` cost type; failure does not lose coins; response updates page/scene data and balance. | `create.html:329`, `.planning/PROJECT.md:59`, `scripts/creator.js:816` |
| Comic/project persistence | Create, reopen, and continue private comics owned by the signed-in user. | Current project title, story, pages, scenes, and history disappear on refresh. | DB stores comic owner, title, story, characters, style, tone, status, timestamps, scenes, pages, prompt metadata, model id, generated image URL/key, and generation cost. Users can list their own comics and fetch one by id. | `.planning/PROJECT.md:30`, `.planning/PROJECT.md:61`, `create.html:31`, `scripts/creator.js:64`, `scripts/creator.js:66`, `.planning/codebase/ARCHITECTURE.md:210` |
| Generated page persistence | Generated images remain available in comic history. | Current code assigns the returned image URL directly to `pages[activePage]`; no durable backend storage exists. | Successful generation stores page metadata and durable image location; reopening a comic restores thumbnails and current page; failed generations store failure status without charging incorrectly. | `scripts/creator.js:605`, `.planning/codebase/CONCERNS.md:176`, `.planning/PROJECT.md:28` |
| AI text assistance behind backend boundary | Use AI story enhancement, scene suggestions, dialogue regeneration, and caption generation without exposing provider secrets. | These are already table-stakes creator actions in the UI and should remain stable while auth/business logic is added. | Existing `/api/ai-text` tasks keep working; requests are validated and rate-limited; task responses can update saved draft state when a comic is open. | `create.html:133`, `create.html:293`, `create.html:322`, `create.html:327`, `scripts/creator.js:395`, `.planning/codebase/ARCHITECTURE.md:84` |
| Profile basics | View current profile, edit display name, and upload/update avatar. | Backend spec requires profile editing; UI already has a profile menu placeholder. | Profile API returns provider-seeded name/avatar; display name edits persist; avatar upload validates type/size and stores object key/URL; old avatar cleanup is handled or documented. | `.planning/PROJECT.md:28`, `.planning/PROJECT.md:31`, `create.html:47`, `create.html:52`, `scripts/creator.js:838` |
| Payment-ready catalog | View seeded coin packages for future purchase: 100, 500, and 1000 coins. | Current milestone must prepare payment tables but not integrate real acquiring. | DB has coin package and payment tables; seed creates 100/500/1000 packages; API lists active packages; no real checkout/webhook is required. | `.planning/PROJECT.md:32`, `.planning/PROJECT.md:71` |
| Production safety gates | Use the creator without exposing secrets, private files, or unlimited AI spend. | Current server can expose repository files and public AI routes spend the server key. | Static serving is locked to public assets; auth protects private APIs; generation/auth routes have basic rate limits; request validation and safe cookies are implemented; critical backend behavior has automated tests. | `.planning/codebase/CONCERNS.md:39`, `.planning/codebase/CONCERNS.md:71`, `.planning/PROJECT.md:33`, `.planning/PROJECT.md:72` |
| Deployment readiness | Run locally and deploy production with documented env vars. | Production URL and cloud operation are part of the backend spec and project requirements. | `.env.example`, local README, production deployment config, migration command, required env list, and health behavior exist; production OAuth callbacks work. | `.planning/PROJECT.md:33`, `.planning/PROJECT.md:60`, `.planning/PROJECT.md:61` |

## Current Creator Capabilities To Preserve

These are already implemented in the browser and should not be regressed while moving state and trust to the backend.

| Current Capability | Backend v1 Treatment | Acceptance Implication | Sources |
|---|---|---|---|
| Edit project title, story, and characters. | Persist as comic draft metadata. | Refresh/reopen preserves title, story, and characters for the user's comic. | `create.html:31`, `create.html:133`, `create.html:151` |
| Select visual style, tone, custom tone, and model. | Persist selected generation settings and validate model server-side. | Backend response records model/style/tone used for each generated page. | `create.html:157`, `create.html:205`, `create.html:217`, `create.html:229`, `scripts/creator.js:548` |
| Add/reorder/edit scenes, dialogue, and captions. | Persist scenes as editable draft data tied to comic id. | Scene edits survive reload and are included in generation payload. | `create.html:293`, `create.html:299`, `create.html:322`, `create.html:327`, `scripts/creator.js:66` |
| Add pages and switch thumbnails. | Persist page records with order and status. | Added pages survive reload; active thumbnails restore from saved page data. | `create.html:342`, `scripts/creator.js:209`, `scripts/creator.js:660` |
| Download current generated page. | Keep as frontend utility using persisted image URL. | Download works after reopening saved comic if image URL/key is valid. | `create.html:91`, `scripts/creator.js:624` |
| Share current project URL. | Keep local/private link behavior only in v1. | Sharing may copy a private URL for the current browser/session, but public publishing is deferred. | `create.html:97`, `scripts/creator.js:636`, `.planning/PROJECT.md:42` |
| Missing OpenRouter config banner. | Replace or supplement with production-safe health/config behavior. | Public health does not leak sensitive config details, while local setup still gives actionable missing-key feedback. | `create.html:15`, `scripts/creator.js:756`, `.planning/codebase/ARCHITECTURE.md:214` |

## Deferred Or Differentiator Work

These should not be part of the v1 production backend milestone unless separately promoted. They are valuable later, but they either exceed the backend spec or would distract from trust, persistence, and billing foundations.

| Deferred/Differentiator | Why Defer | What To Build Instead For v1 | Sources |
|---|---|---|---|
| Full payment provider integration, checkout, webhooks, and real coin purchase fulfillment. | The project explicitly scopes payment-provider integration out while requiring payment-ready tables. | Seed package catalog and payment table shape only. | `.planning/PROJECT.md:36`, `.planning/PROJECT.md:71` |
| Admin panel for users, payments, comics, moderation, or ledger edits. | Out of scope for first backend milestone; role system is also out of scope. | Direct DB/admin scripts can be used during development; normal user APIs only. | `.planning/PROJECT.md:37`, `.planning/PROJECT.md:40` |
| Public profiles, public comic feed, social publishing, likes, comments, follows, or gallery discovery. | Current backend target is private comic history, not a social network. | Keep all comic history private per authenticated owner. | `.planning/PROJECT.md:42` |
| Email campaigns, notification emails, and marketing automation. | No active requirement depends on email. | OAuth-only auth and in-app toasts/status responses. | `.planning/PROJECT.md:38` |
| Password login or custom credential accounts. | Backend spec requires OAuth through Google/Yandex and no separate password flow. | Google and Yandex OAuth only. | `.planning/PROJECT.md:27`, `.planning/PROJECT.md:70` |
| Frontend framework migration. | Current app is static HTML/CSS/JS and the project says to preserve this shape unless a later phase proves otherwise. | Add small API client/state modules only where necessary. | `.planning/PROJECT.md:47`, `.planning/PROJECT.md:53` |
| Real-time generation job dashboard or queue UI. | Useful later for long generations, but not necessary to satisfy v1 user capability if synchronous route remains reliable with timeouts. | Add idempotency, timeouts, persisted generation status, and clear loading/error states. | `.planning/codebase/CONCERNS.md:98`, `scripts/creator.js:578` |
| Advanced model marketplace or per-model dynamic pricing UI. | UI has model cards, but v1 can keep a small validated registry. | Backend model registry with safe metadata and configured generation costs. | `create.html:205`, `create.html:217`, `create.html:229`, `.planning/codebase/CONCERNS.md:25` |
| Collaborative editing and cross-user sharing. | No current requirement; would add authorization and conflict complexity. | Single-owner private comics only. | `.planning/PROJECT.md:42`, `.planning/PROJECT.md:61` |

## Feature Dependencies

```text
OAuth/session -> authenticated creator bootstrap
OAuth/session -> private comic history
OAuth/session -> wallet ownership
Wallet ledger -> protected generation debit
Comic persistence -> generated page persistence
Generated page persistence -> durable comic history
Payment-ready catalog -> future real purchase flow
Static/API safety gates -> production deployment
```

## MVP Recommendation

Prioritize these first:

1. OAuth/session foundation with current-user/profile/wallet bootstrap.
2. Database schema and migrations for users, provider identities, sessions, profiles, wallets, transactions, comics, scenes, pages, coin packages, and payment placeholders.
3. Protected generation flow that validates input, checks balance, persists result/failure, writes transaction ledger, and returns updated balance.
4. Comic history APIs to list, open, create, update, and continue private comics.
5. Production safety gates and tests around auth, static serving, wallet debits, idempotency, insufficient balance, and generation failure.

Defer real payments, social publishing, admin features, framework migration, and public galleries until after the backend can reliably protect accounts, coins, and private generated work.

## Acceptance Implications For Roadmap

- Auth phases must include real provider callback testing, not just mocked session middleware, because production OAuth is an explicit acceptance gate.
- Wallet phases must test negative balance prevention, duplicate request/idempotency behavior, refund/no-debit on failed generation, and transaction-history reconciliation.
- Persistence phases must verify a complete creator round trip: create comic, edit story/scenes/settings, generate page, reload, list comic, reopen comic, and continue editing.
- Frontend adaptation should replace demo state incrementally. The visible UI affordances in `create.html` should keep working while data sources move from `scripts/creator.js` memory to backend APIs.
- Deployment phase must include secure cookie behavior and a safer public static surface before exposing authenticated APIs.

## Sources

- `.planning/PROJECT.md:7` - production-service goal: sign in, profile/coin balance, spend coins, durable comic history.
- `.planning/PROJECT.md:24` - active backend milestone requirements.
- `.planning/PROJECT.md:36` - explicit out-of-scope items.
- `.planning/PROJECT.md:47` - current static frontend and in-memory creator state.
- `.planning/PROJECT.md:51` - backend spec summary.
- `.planning/PROJECT.md:59` - generation costs.
- `.planning/PROJECT.md:60` - secure sessions.
- `.planning/PROJECT.md:61` - persistence source of truth.
- `.planning/codebase/ARCHITECTURE.md:13` - no database/session/persisted project store today.
- `.planning/codebase/ARCHITECTURE.md:84` - AI text flow.
- `.planning/codebase/ARCHITECTURE.md:94` - comic page generation flow.
- `.planning/codebase/ARCHITECTURE.md:208` - auth missing and required.
- `.planning/codebase/ARCHITECTURE.md:210` - persistence missing and required.
- `.planning/codebase/CONCERNS.md:13` - client-only application state.
- `.planning/codebase/CONCERNS.md:19` - demo credits are not business logic.
- `.planning/codebase/CONCERNS.md:39` - unsafe repository-root static serving.
- `.planning/codebase/CONCERNS.md:71` - unauthenticated AI endpoints spend server key.
- `.planning/codebase/CONCERNS.md:171` - production backend features missing.
- `.planning/codebase/CONCERNS.md:176` - generated image persistence missing.
- `backend/BACKEND_TZ.md` - backend spec for OAuth, users/profiles, wallets, comic history, payment-ready tables, deployment, and acceptance criteria.
- `create.html:31` - project title input.
- `create.html:40` - visible credit balance.
- `create.html:52` - profile menu action.
- `create.html:54` - logout action.
- `create.html:133` - story input.
- `create.html:151` - characters input.
- `create.html:157` - style selector.
- `create.html:205` - first image model card.
- `create.html:247` - generate page action.
- `create.html:293` - AI scene suggestion action.
- `create.html:329` - scene regeneration action.
- `create.html:342` - add page action.
- `scripts/creator.js:64` - in-memory pages.
- `scripts/creator.js:66` - in-memory scenes.
- `scripts/creator.js:73` - in-memory credits.
- `scripts/creator.js:395` - AI text API client.
- `scripts/creator.js:548` - generation payload builder.
- `scripts/creator.js:578` - comic page generation flow.
- `scripts/creator.js:613` - client-side credit decrement.
- `scripts/creator.js:624` - page download utility.
- `scripts/creator.js:636` - share utility.
- `scripts/creator.js:660` - add page behavior.
- `scripts/creator.js:756` - health/config check.
