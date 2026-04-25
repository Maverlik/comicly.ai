# Coding Conventions

**Analysis Date:** 2026-04-25

## Naming Patterns

**Files:**
- Use lowercase entry-point files at the project root: `server.js`, `index.html`, `create.html`, `styles.css`, `creator.css`.
- Use lowercase feature scripts under `scripts/`: `scripts/main.js` for the landing carousel and `scripts/creator.js` for the creator workspace.
- Use asset filenames from `assets/` as stable public paths in HTML, CSS, and JavaScript, including names with spaces such as `assets/Dark logo.png`; preserve existing filenames when referencing committed assets.

**Functions:**
- Use `camelCase` for JavaScript functions: `loadEnv`, `sendJson`, `readJson`, `buildImagePrompt`, `extractImageUrl`, `generateComicPage`, `handleAiText`, `serveStatic` in `server.js`; `showToast`, `getSnapshot`, `pushHistory`, `renderScenes`, `callAiText`, `setTab` in `scripts/creator.js`; `normalizeIndex`, `setCarousel`, `moveCarousel` in `scripts/main.js`.
- Use verb-led names for operations that mutate UI or state: `setPage`, `setStyle`, `setTone`, `setModel`, `setScene`, `toggleBusy`, `toggleProfileMenu`, `toggleBurgerMenu` in `scripts/creator.js`.
- Use `handle*` names for server request handlers: `handleAiText` and `handleHealth` in `server.js`.
- Use `async function` declarations for request flows and browser network flows: `callOpenRouter`, `generateComicPage`, `handleAiText` in `server.js`; `callAiText`, `enhanceStory`, `regenerateDialogue`, `generateCaption`, `suggestScenes`, `shareProject`, `checkHealth` in `scripts/creator.js`.

**Variables:**
- Use `camelCase` for mutable browser state and DOM handles: `activePage`, `activeTone`, `activeModel`, `activeScene`, `historyIndex`, `projectTitleInput`, `generatePageButton`, `sceneList`, `comicOutput` in `scripts/creator.js`.
- Use `const` for module-level DOM references and configuration arrays when bindings do not change: `PLACEHOLDER_IMAGES`, `DEFAULT_MODEL_ID`, `toneButtons`, `modelCards` in `scripts/creator.js`.
- Use `let` only for state that changes across interactions: `pages`, `pageImages`, `scenes`, `credits`, `history`, timers, and active indexes in `scripts/creator.js`; `activePage` and `isSwitching` in `scripts/main.js`.
- Use uppercase `SCREAMING_SNAKE_CASE` for constants and maps with shared semantic meaning: `DEFAULT_IMAGE_MODEL`, `DEFAULT_TEXT_MODEL`, `ALLOWED_IMAGE_MODELS`, `TEXT_TASKS` in `server.js`; `DEFAULT_MODEL_ID` and `PLACEHOLDER_IMAGES` in `scripts/creator.js`.

**Types:**
- Not applicable. The codebase is plain JavaScript with no TypeScript type declarations or JSDoc typedefs.
- Represent structured state as plain object literals: page/story snapshots in `getSnapshot` and `restoreSnapshot` in `scripts/creator.js`; API payloads in `buildScenePayload` and `callOpenRouter`.

## Code Style

**Formatting:**
- No formatter config is detected. Missing files include `.prettierrc`, `prettier.config.*`, `biome.json`, and equivalent formatting config.
- Use the repository's existing style manually: two-space indentation, semicolons, double quotes for strings, trailing commas in multiline arrays/objects, and braces around control-flow blocks.
- Keep HTML indentation at two spaces, as used in `index.html` and `create.html`.
- Keep CSS declarations grouped by selector with two-space indentation and multiline property lists, as used in `styles.css` and `creator.css`.
- Preserve the existing dark theme token pattern in CSS: root-level custom properties such as `--bg`, `--panel`, `--line`, `--ink`, `--muted`, `--blue`, and `--font` in `styles.css` and `creator.css`.

**Linting:**
- No linting config is detected. Missing files include `.eslintrc*`, `eslint.config.*`, and `biome.json`.
- `package.json` exposes only `npm start`; there are no `lint`, `format`, or `check` scripts.
- Follow browser-safe plain JavaScript patterns already present in `scripts/creator.js`: optional chaining for nullable DOM elements, explicit `Number(...)` conversions for dataset values, and guarded returns when required DOM elements or state are missing.

## Import Organization

**Order:**
1. Node built-ins first in `server.js`: `node:http`, `node:fs`, `node:path`.
2. Module constants next in `server.js`: `rootDir`, `port`, model constants, `contentTypes`.
3. DOM references first in browser files: `scripts/main.js` and `scripts/creator.js` begin by collecting elements with `document.querySelector` and `document.querySelectorAll`.
4. Mutable UI state after DOM references in `scripts/creator.js`: `pages`, `pageImages`, `scenes`, active indexes, credits, history.
5. Function declarations after state, then event listener wiring and startup calls at the bottom of `scripts/creator.js`.

**Path Aliases:**
- Not detected. There is no build system, module resolver, or import alias configuration.
- Browser scripts are loaded directly by relative paths: `scripts/main.js` in `index.html` and `scripts/creator.js` in `create.html`.
- Static assets are referenced by relative public paths such as `assets/comic-preview-fantasy.png` in `index.html`, `create.html`, `styles.css`, `creator.css`, and `scripts/creator.js`.

## Error Handling

**Patterns:**
- Server endpoints return JSON through the shared `sendJson(response, statusCode, payload)` helper in `server.js`.
- Request body parsing is isolated in `readJson(request)` in `server.js`; invalid JSON and oversized bodies reject with `Error` objects.
- Server request handlers use `try`/`catch` and return `{ error, code }` payloads: `generateComicPage` and `handleAiText` in `server.js`.
- Server validation uses early returns with explicit HTTP status codes: missing `story` returns `400`; missing generated image/text returns `502`; missing API key throws an error with `statusCode = 503` and `code = "MISSING_KEY"` in `server.js`.
- Browser network functions parse JSON defensively with `response.json().catch(() => ({}))` in `scripts/creator.js`.
- Browser request failures become `Error` objects in `callAiText` and `generateComicPage`, then user-facing messages are displayed with `showToast` in `scripts/creator.js`.
- Browser UI functions use guard clauses for absent elements and empty state: `if (!toast) return`, `if (!storyInput) return`, `if (!scenes.length) return`, `if (!pages[index]) return` in `scripts/creator.js`.
- Static file handling in `serveStatic` returns plain text `403`, `404`, or `405` responses in `server.js`.

## Logging

**Framework:** `console`

**Patterns:**
- Server startup logs once with `console.log` in `server.js`.
- No structured logger is detected.
- Browser code avoids console logging and surfaces recoverable problems through `showToast` and `showConfigBanner` in `scripts/creator.js`.
- Use user-facing toast messages for expected interaction failures in `scripts/creator.js`; use server JSON errors for API failures in `server.js`.

## Comments

**When to Comment:**
- Comments are sparse in JavaScript. Add comments only around non-obvious fallback behavior or integration constraints.
- CSS uses large section divider comments in `creator.css` to group UI regions such as app bar, popovers, workspace, tabs, canvas, right panel, busy state, toast, and responsive rules. Follow that section-comment style when adding large CSS regions to `creator.css`.
- Preserve existing inline comments that explain intentional fallback behavior, such as the share cancellation fallback and health check fallback in `scripts/creator.js`.

**JSDoc/TSDoc:**
- Not detected. There are no JSDoc or TSDoc blocks in `server.js`, `scripts/main.js`, or `scripts/creator.js`.
- Prefer clear function names and small helper functions over introducing JSDoc in this codebase unless a function accepts a complex object contract shared across files.

## Function Design

**Size:** Keep focused helpers small where possible, matching `sendJson`, `extractText`, `normalizeTextTone`, `setLoading`, `toggleBusy`, `setTab`, and `setSideTab`. Larger workflow functions are accepted for UI orchestration in `scripts/creator.js`, but keep new workflows composed from smaller helpers.

**Parameters:** Use plain positional parameters for simple helpers, such as `setPage(index, save = true)` and `setTone(tone, save = true, clearCustom = true)` in `scripts/creator.js`. Use object destructuring for option-heavy integration calls, as in `callOpenRouter({ model, messages, modalities, imageConfig })` in `server.js`.

**Return Values:** Use early `return` for guards and completed response handling. Server handlers write responses instead of returning domain objects. Browser UI setters mutate state and DOM, then optionally call `pushHistory`.

## Module Design

**Exports:** Not detected. `server.js`, `scripts/main.js`, and `scripts/creator.js` do not export functions or use ES modules.

**Barrel Files:** Not applicable. There are no module directories or index barrel files.

**File Boundaries:**
- Keep server concerns in `server.js`: environment loading, static serving, API routing, OpenRouter calls, request validation, and JSON responses.
- Keep landing page carousel behavior in `scripts/main.js`.
- Keep creator workspace UI state, DOM rendering, AI calls, history, and event wiring in `scripts/creator.js`.
- Keep landing page styles in `styles.css` and creator workspace styles in `creator.css`.

---

*Convention analysis: 2026-04-25*
