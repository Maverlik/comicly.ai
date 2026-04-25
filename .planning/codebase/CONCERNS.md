# Codebase Concerns

**Analysis Date:** 2026-04-25

## Tech Debt

**Minimal backend acts as static server plus AI proxy:**
- Issue: `server.js` combines `.env` loading, static file serving, OpenRouter proxying, prompt construction, health checks, and routing in one 392-line file.
- Files: `server.js:1`, `server.js:8`, `server.js:87`, `server.js:166`, `server.js:206`, `server.js:280`, `server.js:338`, `server.js:365`
- Impact: Any change to deployment, authentication, billing, routing, or prompt behavior touches the same module. Production backend requirements in `backend/BACKEND_TZ.md` require user auth, coin balances, transaction history, profile data, comic history, and deployment behavior that do not map cleanly onto the current single-file server.
- Fix approach: Split `server.js` into explicit modules: config/env loader, static serving, API router, OpenRouter client, request validation, and feature handlers. Keep AI route contracts stable while moving implementation behind small functions.

**Client-only application state:**
- Issue: Project title, story, pages, scenes, generated image URLs, history, and credit balance live only in browser variables.
- Files: `scripts/creator.js:64`, `scripts/creator.js:66`, `scripts/creator.js:73`, `scripts/creator.js:104`, `scripts/creator.js:126`, `scripts/creator.js:605`, `scripts/creator.js:613`
- Impact: Refreshing the page loses work and generated outputs. The app cannot support authenticated users, cross-device projects, or comic history until this state moves behind APIs and durable storage.
- Fix approach: Introduce server-owned comic/project entities and persist pages, scenes, prompt metadata, model IDs, image URLs, and credit transactions. Treat browser state as an editable draft cache only.

**Credits are demo UI state, not business logic:**
- Issue: The visible balance starts at `240`, decreases on the client after generation, and can be incremented by an unused `addCredits()` helper.
- Files: `create.html:40`, `scripts/creator.js:73`, `scripts/creator.js:613`, `scripts/creator.js:668`, `backend/BACKEND_TZ.md:36`, `backend/BACKEND_TZ.md:37`, `backend/BACKEND_TZ.md:38`
- Impact: Users can generate after reaching zero because the server does not check balance, and any billing logic can be bypassed by browser edits or direct API calls.
- Fix approach: Move all credit reads, debits, refunds, and transaction logs to backend APIs. Return the updated balance from successful generation calls and block insufficient-balance requests server-side.

**Hardcoded AI model configuration is duplicated:**
- Issue: UI model cards and server allowed models are hardcoded separately; the server fallback default is also separate from the selectable UI default.
- Files: `create.html:205`, `create.html:217`, `create.html:229`, `scripts/creator.js:67`, `server.js:34`, `server.js:37`, `server.js:215`
- Impact: Model names, prices, quality labels, and support flags can drift between frontend and backend. The default `google/gemini-2.5-flash-image-preview` is not listed in the UI model cards or `ALLOWED_IMAGE_MODELS`.
- Fix approach: Create one model registry on the backend and expose safe metadata to the UI. Keep provider IDs, modality support, price, labels, and default selection in one source.

**Large unmodular frontend files:**
- Issue: The creator page behavior is implemented as one 900-line script and one 1179-line stylesheet, with tightly coupled DOM selectors and global mutable variables.
- Files: `scripts/creator.js:1`, `scripts/creator.js:64`, `scripts/creator.js:771`, `creator.css:1`, `create.html:1`
- Impact: Adding project persistence, auth, billing, or richer editor behavior requires coordinated edits across large files and increases regression risk.
- Fix approach: Split by concern: API client, project state/history, scene editor, page strip, account/menu UI, credits, and generation workflow. Keep shared selectors or component roots localized.

## Known Bugs

**Static server may serve secrets and internal files:**
- Symptoms: Any file under the repository root can be requested through the static route if it exists and is a regular file.
- Files: `server.js:5`, `server.js:8`, `server.js:9`, `server.js:338`, `server.js:343`, `server.js:350`, `.gitignore:1`
- Trigger: Start the app with `npm start` and request paths such as `/.env` when a local `.env` exists, `/package.json`, `/backend/BACKEND_TZ.md`, or files under `.planning/`.
- Workaround: Do not deploy this static server as-is. Serve only an explicit public directory and deny dotfiles, planning docs, backend docs, package metadata, and secret/config paths.

**Credit balance does not block generation at zero:**
- Symptoms: The UI reduces credits with `Math.max(0, credits - 20)` after success but never checks balance before sending `/api/generate-comic-page`.
- Files: `scripts/creator.js:578`, `scripts/creator.js:589`, `scripts/creator.js:613`, `create.html:40`
- Trigger: Generate enough pages to reduce credits to zero, then generate again; the frontend still sends the request and the backend still calls OpenRouter.
- Workaround: None in current code. Add server-side balance validation before calling OpenRouter.

**Long OpenRouter calls can leave requests and UI hanging:**
- Symptoms: `fetch()` calls have no timeout or abort behavior on either the server OpenRouter request or browser API requests.
- Files: `server.js:184`, `scripts/creator.js:397`, `scripts/creator.js:589`, `scripts/creator.js:758`
- Trigger: OpenRouter or the local server stalls without returning an error.
- Workaround: Restarting the page or server clears the immediate hang. Add `AbortController` timeouts and user-visible retry states.

**HEAD requests are handled like GET requests:**
- Symptoms: The server routes `HEAD` to `serveStatic()`, which streams the file body instead of ending after headers.
- Files: `server.js:338`, `server.js:358`, `server.js:361`, `server.js:381`
- Trigger: Send `HEAD /index.html`.
- Workaround: Handle `HEAD` separately by writing headers and ending without `fs.createReadStream(...).pipe(response)`.

## Security Considerations

**Repository-root static serving exposes sensitive paths:**
- Risk: A production `.env` file, planning docs, backend specs, or other non-public files can become web-accessible.
- Files: `server.js:5`, `server.js:338`, `server.js:343`, `server.js:350`, `.gitignore:1`
- Current mitigation: A prefix check prevents obvious traversal outside `rootDir`, but there is no public-directory allowlist or dotfile denylist.
- Recommendations: Serve from a dedicated `public/` directory or an explicit file map. Reject dotfiles, `.planning/`, `backend/`, package metadata, and unknown extensions. Normalize with `path.resolve()` and require the resolved path to remain inside the public directory plus a path separator boundary.

**Unauthenticated AI endpoints spend the server API key:**
- Risk: Any visitor can call AI generation endpoints and consume OpenRouter credits through the server-side `OPENROUTER_API_KEY`.
- Files: `server.js:166`, `server.js:184`, `server.js:206`, `server.js:280`, `server.js:371`, `server.js:376`
- Current mitigation: Request body size is capped at roughly 1 MB in `readJson()`.
- Recommendations: Add authentication, per-user and per-IP rate limits, server-side credit checks, request idempotency keys, and audit logging before calling OpenRouter.

**Security headers are missing for static responses:**
- Risk: Browser protections such as CSP, MIME sniffing protection, referrer control, and HSTS are absent.
- Files: `server.js:55`, `server.js:358`, `index.html:218`, `create.html:354`
- Current mitigation: JSON responses set `Cache-Control: no-store`; static responses only set `Content-Type`.
- Recommendations: Add `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and production `Strict-Transport-Security`. Keep the CSP compatible with local assets and the OpenRouter-returned image strategy.

**Health endpoint reveals operational configuration:**
- Risk: `/api/health` discloses whether an API key is configured and which model IDs are active.
- Files: `server.js:329`, `server.js:332`, `server.js:333`, `server.js:334`, `scripts/creator.js:756`
- Current mitigation: It does not reveal the key value.
- Recommendations: Keep public health responses minimal, for example `{ ok: true }`. Move configuration diagnostics to an authenticated admin/debug path.

**HTML injection risk around generated image URLs:**
- Risk: `renderPageStrip()` inserts `src` into an HTML string. Current data comes from placeholders or OpenRouter response URLs, but it is still external data once `pages[activePage]` is assigned from `data.imageUrl`.
- Files: `scripts/creator.js:217`, `scripts/creator.js:605`, `scripts/creator.js:608`
- Current mitigation: Scene text uses `escapeHtml()`, but image URLs in `button.innerHTML` are not escaped as attributes.
- Recommendations: Build DOM nodes with `document.createElement("img")` and assign `img.src` as a property. Validate image URL schemes from OpenRouter before storing them.

## Performance Bottlenecks

**Undo history can retain large generated images:**
- Problem: `pushHistory()` stores snapshots containing `pages`, and `pages` may contain data URLs or large external image strings.
- Files: `scripts/creator.js:104`, `scripts/creator.js:115`, `scripts/creator.js:126`, `scripts/creator.js:135`, `scripts/creator.js:605`
- Cause: Up to 60 snapshots are kept in memory with full page arrays.
- Improvement path: Store lightweight page IDs or URLs in history, cap data URL size, and move binary/image persistence outside the undo stack.

**Static assets are served without cache headers:**
- Problem: Large PNG assets and CSS/JS files are revalidated or refetched without explicit immutable caching behavior.
- Files: `server.js:338`, `server.js:358`, `assets/comicly-hero-bg.png`, `assets/comic-preview-fantasy.png`, `assets/comic-preview-japan.png`, `assets/comic-preview-action.png`
- Cause: `serveStatic()` only sets `Content-Type`.
- Improvement path: Add cache headers for fingerprinted assets, or serve assets through a production static host/CDN that handles caching and compression.

**AI generation is synchronous per HTTP request:**
- Problem: Browser requests stay open while OpenRouter generation runs.
- Files: `server.js:184`, `server.js:206`, `scripts/creator.js:589`
- Cause: There is no job queue, polling endpoint, timeout, or retry boundary.
- Improvement path: For production, use a generation job model with persisted status, idempotency keys, timeout handling, and background workers.

## Fragile Areas

**Path containment check is string-prefix based:**
- Files: `server.js:343`, `server.js:344`
- Why fragile: `startsWith(rootDir)` is easy to misuse and does not enforce a path-segment boundary. Future root/public path changes can accidentally allow sibling-prefix paths.
- Safe modification: Use `path.resolve(publicDir, relativePath)` and verify `resolved === publicDir || resolved.startsWith(publicDir + path.sep)` after rejecting absolute paths and dot segments.
- Test coverage: No tests exercise traversal, encoded paths, dotfiles, or static deny rules.

**Scene and page editor state is tightly coupled to DOM structure:**
- Files: `scripts/creator.js:1`, `scripts/creator.js:208`, `scripts/creator.js:284`, `scripts/creator.js:578`, `create.html:247`, `create.html:314`
- Why fragile: Many selectors are read at module load and functions assume specific markup/data attributes. Markup changes can silently break behavior because optional chaining hides missing elements.
- Safe modification: Add small initialization assertions for required controls and split UI regions into isolated setup functions.
- Test coverage: No DOM tests cover scene editing, generation, page switching, undo/redo, or mobile menu behavior.

**Prompt construction mixes raw user input and business rules:**
- Files: `server.js:87`, `server.js:99`, `server.js:106`, `server.js:114`, `server.js:249`
- Why fragile: Prompt wording, user-provided story/characters/dialogue, page layout constraints, and Russian fallback behavior are concatenated directly. Changes can affect model outputs across all generation flows.
- Safe modification: Treat prompts as versioned templates, validate payload fields, bound individual text fields, and log prompt template versions with generated pages.
- Test coverage: No tests assert prompt shape, required fields, or fallback behavior for malformed scene arrays.

## Scaling Limits

**No database or durable storage:**
- Current capacity: One browser session with volatile in-memory state and OpenRouter-returned image URLs.
- Limit: User accounts, project history, credit ledgers, generated image retention, and cross-device access are not supported.
- Scaling path: Add a database schema for users, sessions, wallets, transactions, comics, pages, and generation jobs; add object storage for generated images.

**No authentication or authorization layer:**
- Current capacity: Public demo-style app.
- Limit: Private comics, user profiles, billing, and production credit controls cannot be enforced.
- Scaling path: Implement OAuth/session handling described in `backend/BACKEND_TZ.md:7`, `backend/BACKEND_TZ.md:41`, and `backend/BACKEND_TZ.md:42` before exposing private or billable workflows.

**No rate limiting or abuse controls:**
- Current capacity: Unlimited calls to `/api/generate-comic-page` and `/api/ai-text` from any client.
- Limit: A single user or script can exhaust OpenRouter quota or overload the Node process.
- Scaling path: Add per-IP and per-user limits, request idempotency, queue depth limits, and model-specific quotas.

## Dependencies at Risk

**No lockfile or test/build toolchain:**
- Risk: `package.json` has only `npm start`, no lockfile, no lint script, no test script, and no dependency-managed server framework.
- Impact: Future dependency additions can become non-reproducible, and regressions are easy to ship without an automated gate.
- Migration plan: Add a lockfile when dependencies are introduced, then add `test`, `lint`, and `check` scripts before expanding backend complexity.

**Runtime depends on Node 22 global APIs:**
- Risk: The server relies on global `fetch()` and declares `node >=22`.
- Impact: Deployments pinned to older Node runtimes fail or need polyfills.
- Migration plan: Keep deployment runtime pinned to Node 22+ or introduce a supported HTTP client dependency with explicit timeout controls.

**OpenRouter response-shape parsing is heuristic:**
- Risk: Image and text extraction scans several possible fields from `choices[0].message`.
- Impact: Provider response changes can produce false 502s even when a generation succeeds.
- Migration plan: Add provider/model-specific adapters with fixture tests for known response shapes.

## Missing Critical Features

**Production backend features are specified but not implemented:**
- Problem: Auth, user profiles, server-side credit balances, credit transaction logs, comic history, payments-ready tables, and deployment behavior are documented requirements, while current code provides only static pages and AI proxy endpoints.
- Blocks: Production launch, billing, private projects, saved comics, profile management, and auditability.
- Files: `backend/BACKEND_TZ.md:5`, `backend/BACKEND_TZ.md:7`, `backend/BACKEND_TZ.md:8`, `backend/BACKEND_TZ.md:9`, `backend/BACKEND_TZ.md:31`, `server.js:365`

**No generated image persistence:**
- Problem: Successful image URLs are assigned directly to `pages[activePage]`; there is no download, copy, or storage step on the backend.
- Blocks: Reliable comic history and long-lived project restoration.
- Files: `scripts/creator.js:605`, `server.js:240`, `backend/BACKEND_TZ.md:30`, `backend/BACKEND_TZ.md:31`

**No deployment configuration:**
- Problem: The repo has no detected production config such as Dockerfile, Vercel config, CI workflow, or deployment README.
- Blocks: Repeatable production deployment and environment setup.
- Files: `package.json:5`, `package.json:6`, `backend/BACKEND_TZ.md:11`, `backend/BACKEND_TZ.md:31`

## Test Coverage Gaps

**No automated tests are present:**
- What's not tested: Server routing, static path safety, OpenRouter request construction, response extraction, request validation, frontend editor behavior, credit UI behavior, and error states.
- Files: `package.json:5`, `server.js`, `scripts/creator.js`, `scripts/main.js`
- Risk: Security regressions and billing bugs can ship undetected.
- Priority: High

**AI route behavior lacks fixtures:**
- What's not tested: `extractImageUrl()`, `extractText()`, AI scenes JSON parsing, OpenRouter error propagation, and no-image responses.
- Files: `server.js:116`, `server.js:143`, `server.js:280`, `server.js:307`
- Risk: Provider response changes break generation silently for users.
- Priority: High

**Frontend workflows lack browser coverage:**
- What's not tested: Generate page, suggest scenes, edit scene fields, undo/redo, add page, download, share fallback, menu toggles, and missing-key banner.
- Files: `create.html`, `scripts/creator.js:208`, `scripts/creator.js:395`, `scripts/creator.js:578`, `scripts/creator.js:756`, `scripts/creator.js:814`
- Risk: DOM or CSS changes can break primary workflows without syntax errors.
- Priority: High

---

*Concerns audit: 2026-04-25*
