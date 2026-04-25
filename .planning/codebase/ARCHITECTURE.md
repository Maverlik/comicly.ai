# Architecture

**Analysis Date:** 2026-04-25

## Pattern Overview

**Overall:** Static multi-page frontend with a small Node.js BFF/static server

**Key Characteristics:**
- Browser pages are plain HTML/CSS/JavaScript with no bundler, framework, or module system. Use `index.html`, `create.html`, `styles.css`, `creator.css`, `scripts/main.js`, and `scripts/creator.js` directly.
- `server.js` owns both static asset delivery and JSON API routes. It uses Node built-ins (`node:http`, `node:fs`, `node:path`) instead of Express or middleware.
- AI generation is proxied server-side through OpenRouter in `server.js`, keeping `OPENROUTER_API_KEY` out of browser code.
- Runtime creator state is held in browser memory in `scripts/creator.js`; there is no database, session layer, or persisted project store in current runtime code.
- UI behavior is bound through `data-*` attributes in `create.html` and `index.html`, then queried by `scripts/creator.js` and `scripts/main.js`.

## Layers

**Static Pages:**
- Purpose: Define page markup, content, and DOM hooks for runtime JavaScript.
- Location: `index.html`, `create.html`
- Contains: Landing-page sections, creator workspace panels, form controls, buttons, `data-*` binding attributes, and script/style tags.
- Depends on: CSS in `styles.css` and `creator.css`, images in `assets/`, browser APIs, and scripts in `scripts/`.
- Used by: `server.js` static file serving and direct browser navigation.

**Presentation Styles:**
- Purpose: Provide all layout, visual styling, responsive behavior, and state classes.
- Location: `styles.css`, `creator.css`
- Contains: CSS custom properties, page layout classes, component classes, state selectors like `.is-active`, `.is-selected`, `[hidden]`, and responsive media queries.
- Depends on: Class names and data/state attributes declared in `index.html`, `create.html`, `scripts/main.js`, and `scripts/creator.js`.
- Used by: Browser rendering for landing and creator pages.

**Landing Page Interaction:**
- Purpose: Rotate the landing-page comic preview carousel.
- Location: `scripts/main.js`
- Contains: Carousel state (`activePage`, `isSwitching`), slot calculation, button disabling, and click handlers.
- Depends on: `data-carousel-card`, `data-carousel-prev`, `data-carousel-next`, `data-page`, and `data-slot` in `index.html`.
- Used by: `index.html` through `<script src="scripts/main.js"></script>`.

**Creator Workspace Interaction:**
- Purpose: Manage the comic creator UI, form state, history, scene editing, page thumbnails, AI calls, and utility actions.
- Location: `scripts/creator.js`
- Contains: DOM references, in-memory arrays for `pages` and `scenes`, selected style/tone/model state, undo/redo history snapshots, rendering functions, fetch wrappers, and event registrations.
- Depends on: DOM hooks in `create.html`, assets in `assets/`, and API routes in `server.js`.
- Used by: `create.html` through `<script src="scripts/creator.js"></script>`.

**HTTP Server and API Layer:**
- Purpose: Serve static files and expose JSON API endpoints for health, image generation, and text generation.
- Location: `server.js`
- Contains: Environment loading, content type mapping, JSON response helpers, request body parsing, OpenRouter request logic, route dispatch, static file resolution, and server startup.
- Depends on: Node.js built-ins, global `fetch`, environment variables, and OpenRouter API responses.
- Used by: `npm start`, browser fetch calls in `scripts/creator.js`, and direct browser requests for static files.

**Asset Layer:**
- Purpose: Store committed raster logos and comic reference images used by both pages.
- Location: `assets/`
- Contains: `assets/full_dark_logo.png`, `assets/full_light_logo.png`, `assets/comicly-hero-bg.png`, `assets/comic-preview-fantasy.png`, `assets/comic-preview-japan.png`, `assets/comic-preview-action.png`, `assets/comicly-reference.png`, and logo variants.
- Depends on: No code dependencies.
- Used by: `index.html`, `create.html`, `styles.css`, and `scripts/creator.js`.

**Backend Requirements Document:**
- Purpose: Capture product/backend requirements for auth, coins, persistence, deployment, and production behavior.
- Location: `backend/BACKEND_TZ.md`
- Contains: Target API/domain requirements and acceptance criteria.
- Depends on: Current runtime surface described in `server.js`, `create.html`, and `scripts/creator.js`.
- Used by: Planning and implementation work; it is not loaded by runtime code.

## Data Flow

**Landing Carousel Flow:**

1. `index.html` renders three `.comic-sheet` cards with `data-carousel-card`, `data-page`, and initial `data-slot` attributes.
2. `scripts/main.js` reads those cards, stores `activePage`, and binds `data-carousel-prev` and `data-carousel-next` click handlers.
3. On click, `moveCarousel()` guards with `isSwitching`, disables navigation buttons, calls `setCarousel()`, and updates each card's `data-slot`.
4. `styles.css` selectors for `.comic-sheet[data-slot="main"]`, `[data-slot="left"]`, and `[data-slot="right"]` drive the visible carousel positions.

**Creator UI State Flow:**

1. `create.html` renders static controls and empty dynamic containers such as `data-scene-list`, `.page-strip`, `data-comic-output`, and `data-toast`.
2. `scripts/creator.js` creates initial in-memory state: `pages`, `pageImages`, `scenes`, `activePage`, `activeTone`, `activeModel`, `activeScene`, `credits`, and `history`.
3. Initialization calls `renderPageStrip()`, `renderScenes()`, `setPage()`, `setStyle()`, `setTone()`, `setModel()`, `setTab()`, `setSideTab()`, `pushHistory()`, and `checkHealth()`.
4. User actions mutate memory state through functions such as `setPage()`, `setStyle()`, `setTone()`, `setModel()`, `addScene()`, `moveScene()`, `syncSceneFromInputs()`, `addPage()`, and `addCredits()`.
5. UI refresh is immediate DOM mutation from `scripts/creator.js`; no client-side store or persistence abstraction exists.

**AI Text Flow:**

1. User actions in `create.html` trigger `enhanceStory()`, `suggestScenes()`, `regenerateDialogue()`, or `generateCaption()` in `scripts/creator.js`.
2. `callAiText(task)` builds a JSON payload from current story, characters, selected scene, style, and tone.
3. Browser code sends `POST /api/ai-text` to `server.js`.
4. `server.js` dispatches to `handleAiText()`, validates `payload.task` and `payload.story`, selects a task from `TEXT_TASKS`, and calls `callOpenRouter()`.
5. `callOpenRouter()` sends a chat completion request to OpenRouter and returns model output.
6. `handleAiText()` extracts text with `extractText()`. For `task === "scenes"`, it parses a JSON array before responding.
7. `scripts/creator.js` applies the response to form fields or the `scenes` array, rerenders, pushes history, and shows a toast.

**Comic Page Generation Flow:**

1. User clicks the generate or regenerate button in `create.html`.
2. `generateComicPage()` in `scripts/creator.js` calls `buildScenePayload()` to serialize story, characters, style, tone, selected model, active page, selected scene, scene prompts, dialogue, caption, and layout direction.
3. Browser code sends `POST /api/generate-comic-page` to `server.js`.
4. `server.js` dispatches to `generateComicPage()`, validates `payload.story`, normalizes the requested model against `ALLOWED_IMAGE_MODELS`, builds an image prompt with `buildImagePrompt()`, and calls `callOpenRouter()`.
5. `extractImageUrl()` reads the image URL or data URL from supported OpenRouter response shapes.
6. `server.js` returns `{ imageUrl, model, text }` as JSON.
7. `scripts/creator.js` replaces `pages[activePage]`, updates `data-comic-output`, updates the active thumbnail, decrements the in-memory `credits`, pushes history, and shows a toast.

**Static File Flow:**

1. Browser requests `/`, `/index.html`, `/create.html`, CSS, JS, or assets.
2. `server.js` maps `/` to `/index.html` inside `serveStatic()`.
3. `serveStatic()` normalizes the path against `rootDir`, rejects path traversal when the result does not start with `rootDir`, checks that the target is a file, and streams it with a content type from `contentTypes`.

**State Management:**
- Use plain module-level variables in `scripts/creator.js` for creator state.
- Use complete snapshots from `getSnapshot()` for undo/redo; `pushHistory()` stores up to 60 snapshots and `restoreSnapshot()` rehydrates DOM state.
- Use DOM attributes and classes as UI state markers: `.is-active`, `.is-selected`, `aria-selected`, `aria-checked`, `hidden`, and `data-slot`.
- Use no localStorage, cookies, session state, database state, or server-side project state in runtime code.

## Key Abstractions

**Route Dispatcher:**
- Purpose: Map HTTP method/path pairs to handlers.
- Examples: `server.js`
- Pattern: Single `http.createServer()` callback with explicit `if` branches for `GET /api/health`, `POST /api/generate-comic-page`, `POST /api/ai-text`, static `GET`/`HEAD`, and fallback `405`.

**OpenRouter Client Function:**
- Purpose: Centralize outbound AI calls and secret-bearing headers.
- Examples: `server.js`
- Pattern: `callOpenRouter({ model, messages, modalities, imageConfig })` creates a request body, adds optional image parameters, sends `fetch()` to `https://openrouter.ai/api/v1/chat/completions`, normalizes error handling, and returns parsed JSON.

**AI Task Registry:**
- Purpose: Keep text-generation prompts and response length hints grouped by task.
- Examples: `server.js`
- Pattern: `TEXT_TASKS` maps `enhance`, `dialogue`, `caption`, and `scenes` to `system`, `instruction(payload)`, and `max` fields.

**Creator State Snapshot:**
- Purpose: Support undo/redo for the workspace.
- Examples: `scripts/creator.js`
- Pattern: `getSnapshot()`, `pushHistory()`, and `restoreSnapshot()` copy primitive state, arrays, and scene objects; `isRestoring` prevents recursive history writes.

**Scene Model:**
- Purpose: Represent editable story beats for generation.
- Examples: `scripts/creator.js`, `create.html`
- Pattern: Scene objects use `{ title, description, dialogue, caption }` and are rendered into `.scene-item` elements in `renderScenes()`.

**Page Model:**
- Purpose: Represent generated or placeholder comic pages.
- Examples: `scripts/creator.js`, `create.html`
- Pattern: `pages` is an array of image URLs or generated placeholder data URLs; thumbnails are rebuilt by `renderPageStrip()`.

**DOM Binding Contract:**
- Purpose: Decouple scripts from text content by using IDs and `data-*` hooks.
- Examples: `create.html`, `index.html`, `scripts/creator.js`, `scripts/main.js`
- Pattern: Add stable IDs for form controls (`#storyInput`, `#styleSelect`) and `data-*` selectors for actions and dynamic regions (`data-generate-page`, `data-scene-list`, `data-tab`, `data-side-pane`).

**Static Asset Contract:**
- Purpose: Share visual assets across pages and placeholder UI.
- Examples: `assets/`, `index.html`, `create.html`, `scripts/creator.js`
- Pattern: Assets are referenced by relative paths such as `assets/comic-preview-fantasy.png`; generated page URLs replace placeholders only at runtime.

## Entry Points

**Node Server:**
- Location: `server.js`
- Triggers: `npm start` from `package.json`
- Responsibilities: Load environment variables from `.env` when present, start the HTTP server on `PORT` or `3000`, serve files from the project root, expose API routes, proxy AI calls to OpenRouter, and return JSON errors.

**Landing Page:**
- Location: `index.html`
- Triggers: Browser request for `/` or `/index.html`
- Responsibilities: Render the marketing/overview page, link to `create.html`, show sample comic images, and load `scripts/main.js`.

**Landing Carousel Script:**
- Location: `scripts/main.js`
- Triggers: Loaded by `index.html`
- Responsibilities: Initialize carousel slots, bind carousel navigation, and update `data-slot` attributes.

**Creator Page:**
- Location: `create.html`
- Triggers: Browser request for `/create.html` or navigation from `index.html`
- Responsibilities: Render the creator workspace shell, controls, panels, dynamic containers, config banner, and load `scripts/creator.js`.

**Creator Workspace Script:**
- Location: `scripts/creator.js`
- Triggers: Loaded by `create.html`
- Responsibilities: Initialize in-memory state, bind all workspace interactions, call API routes, render dynamic scene/page UI, and manage undo/redo and notifications.

**Stylesheets:**
- Location: `styles.css`, `creator.css`
- Triggers: Linked by `index.html` and `create.html`
- Responsibilities: Define visual system, layout, responsive behavior, component states, and animation/loading states.

## Error Handling

**Strategy:** Return normalized JSON errors from API routes, use toast notifications and config banners in the browser, and allow static file failures to return HTTP status codes.

**Patterns:**
- `server.js` uses `sendJson(response, statusCode, payload)` for all API JSON responses with `Cache-Control: no-store`.
- `readJson(request)` rejects invalid JSON and bodies larger than 1 MB.
- `generateComicPage()` and `handleAiText()` wrap route work in `try/catch`, prefer `error.statusCode`, and include `error.code` when present.
- `callOpenRouter()` raises `MISSING_KEY` with status `503` when `OPENROUTER_API_KEY` is absent.
- `scripts/creator.js` catches failed `fetch()` responses, extracts `data.error`, shows `showConfigBanner()` for `MISSING_KEY`, and displays errors with `showToast()`.
- `serveStatic()` returns `403` for paths outside `rootDir`, `404` for missing/non-file paths, and `405` for unsupported methods in the server dispatcher.

## Cross-Cutting Concerns

**Logging:** `server.js` logs only startup with `console.log()`. Runtime request logging, structured logs, and error logs are not implemented.

**Validation:** `server.js` validates required `story`, known text task names, image model allow-list membership, JSON parseability, and request body size. `scripts/creator.js` performs client-side presence checks before AI calls.

**Authentication:** Runtime authentication is not implemented. `create.html` contains demo profile markup and `scripts/creator.js` contains demo profile actions. `backend/BACKEND_TZ.md` defines requirements for Google/Yandex auth and server sessions.

**Persistence:** Runtime persistence is not implemented. `scripts/creator.js` holds pages, scenes, credits, and history in memory. `backend/BACKEND_TZ.md` defines requirements for database-backed users, coins, transactions, comic history, and generated pages.

**Configuration:** `server.js` reads `.env` when present and uses environment variables such as `PORT`, `OPENROUTER_API_KEY`, `OPENROUTER_SITE_URL`, `OPENROUTER_APP_NAME`, `OPENROUTER_IMAGE_MODEL`, `OPENROUTER_TEXT_MODEL`, and `OPENROUTER_IMAGE_ASPECT_RATIO`. `.env.example` is present for documented configuration shape.

**Security Boundary:** API secrets belong in server environment variables and are only used in `server.js`. Browser code in `scripts/creator.js` calls local API routes instead of OpenRouter directly.

---

*Architecture analysis: 2026-04-25*
