# Codebase Structure

**Analysis Date:** 2026-04-25

## Directory Layout

```text
comicly.ai/
├── .planning/              # GSD planning and generated codebase intelligence
├── assets/                 # Committed logo, hero, reference, and preview raster images
├── backend/                # Backend requirements/specification documents
├── scripts/                # Plain browser JavaScript loaded directly by HTML pages
├── .env.example            # Example environment configuration; do not place secrets here
├── .gitignore              # Git ignore rules
├── create.html             # Creator workspace HTML entry point
├── creator.css             # Creator workspace stylesheet
├── index.html              # Landing page HTML entry point
├── package.json            # Node package metadata and start script
├── server.js               # Node HTTP server, static file server, and AI API proxy
└── styles.css              # Landing page stylesheet
```

## Directory Purposes

**Project Root:**
- Purpose: Host all runtime files directly because there is no build step or framework directory convention.
- Contains: HTML entry points, page-specific CSS, `server.js`, `package.json`, `.env.example`, and high-level folders.
- Key files: `server.js`, `index.html`, `create.html`, `package.json`, `.env.example`

**`.planning/`:**
- Purpose: Store GSD project planning artifacts and codebase maps.
- Contains: Generated and maintained planning documents.
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`
- Add mapper output under `.planning/codebase/` only when producing codebase intelligence.

**`assets/`:**
- Purpose: Store committed image assets referenced by pages, styles, and scripts.
- Contains: PNG logos, hero/background imagery, comic preview pages, and style reference images.
- Key files: `assets/full_dark_logo.png`, `assets/full_light_logo.png`, `assets/comicly-hero-bg.png`, `assets/comic-preview-fantasy.png`, `assets/comic-preview-japan.png`, `assets/comic-preview-action.png`, `assets/comicly-reference.png`
- Add new static images here and reference them with relative paths like `assets/name.png`.

**`backend/`:**
- Purpose: Store backend product and architecture requirements.
- Contains: Markdown requirements/specification documents.
- Key files: `backend/BACKEND_TZ.md`
- Do not place runtime backend code here unless the project introduces a real backend module structure; current runtime backend is `server.js`.

**`scripts/`:**
- Purpose: Store browser scripts loaded directly by HTML pages.
- Contains: Plain JavaScript files with page-level behavior.
- Key files: `scripts/main.js`, `scripts/creator.js`
- Add page-specific browser behavior here when it is loaded by a matching HTML file through a normal `<script src="scripts/name.js"></script>` tag.

## Key File Locations

**Entry Points:**
- `server.js`: Node startup file, HTTP router, static file server, and OpenRouter proxy.
- `index.html`: Public landing page entry point served for `/` and `/index.html`.
- `create.html`: Creator workspace entry point served for `/create.html`.
- `scripts/main.js`: Landing page carousel entry script.
- `scripts/creator.js`: Creator workspace entry script and main application logic.

**Configuration:**
- `package.json`: Defines package name, `npm start`, and Node engine requirement `>=22`.
- `.env.example`: Documents environment variables for local configuration; do not read or commit real `.env` values.
- `server.js`: Reads `.env` when present and uses environment variables for port and OpenRouter configuration.

**Core Logic:**
- `server.js`: API route dispatch, JSON parsing, model selection, prompt building, OpenRouter calls, image/text extraction, and static serving.
- `scripts/creator.js`: Creator state model, scene model, page model, undo/redo history, DOM rendering, event handlers, AI fetch calls, and user feedback.
- `scripts/main.js`: Landing carousel state and DOM state mutation.

**UI Markup:**
- `index.html`: Landing header, hero, preview carousel, workflow section, feature grid, pricing band, and footer.
- `create.html`: Config banner, app bar, left settings panel, comic canvas, right scene/dialogue panel, page strip, and toast container.

**Styling:**
- `styles.css`: Landing-page variables, global styles, hero layout, preview carousel styles, workflow/features/pricing/footer styles, and responsive rules.
- `creator.css`: Creator-page variables, app shell, panels, popovers, buttons, inputs, canvas, page strip, scene list, tabs, toast, loading states, and responsive rules.

**Assets:**
- `assets/full_dark_logo.png`: Logo used by `index.html` and `create.html`.
- `assets/comic-preview-fantasy.png`: Landing carousel sample and creator placeholder/reference image.
- `assets/comic-preview-japan.png`: Landing carousel sample and creator placeholder/reference image.
- `assets/comic-preview-action.png`: Landing carousel sample and creator placeholder/reference image.
- `assets/comicly-reference.png`: Style swatch/reference image.
- `assets/comicly-hero-bg.png`: Hero/background asset available in `assets/`.

**Planning/Requirements:**
- `backend/BACKEND_TZ.md`: Requirements for production backend features such as OAuth, coins, database persistence, payments preparation, deployment, and acceptance criteria.

**Testing:**
- Not detected. There are no `*.test.*`, `*.spec.*`, Jest, Vitest, Playwright, or test configuration files in the current project structure.

## Naming Conventions

**Files:**
- HTML entry points use concise lowercase names at root: `index.html`, `create.html`.
- Page-specific styles use root-level CSS names matching the page role: `styles.css` for `index.html`, `creator.css` for `create.html`.
- Browser scripts use lowercase page/domain names under `scripts/`: `scripts/main.js`, `scripts/creator.js`.
- Static assets use descriptive names under `assets/`; current names include both kebab-style names such as `assets/comic-preview-action.png` and spaced logo names such as `assets/Dark logo.png`.
- Planning docs use uppercase Markdown names under `.planning/codebase/`: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`.

**Directories:**
- Top-level directories are lowercase and domain-oriented: `assets/`, `backend/`, `scripts/`.
- Generated planning intelligence belongs under `.planning/codebase/`.

**HTML Hooks:**
- Use IDs for unique form controls referenced by JavaScript: `#projectTitle`, `#storyInput`, `#styleSelect`, `#customToneInput`, `#zoomSelect`, `#sceneTitleInput`, `#sceneDescriptionInput`, `#dialogueInput`, `#captionInput`.
- Use `data-*` attributes for behavior and dynamic regions: `data-generate-page`, `data-suggest-scenes`, `data-scene-list`, `data-comic-output`, `data-tab`, `data-side-tab`, `data-carousel-card`.
- Use ARIA attributes with interactive controls in `create.html` and `index.html`, especially tabs, radio-like model cards, menus, and icon buttons.

**CSS Classes:**
- Use semantic page/component class names: `.site-header`, `.hero`, `.showcase`, `.creator-shell`, `.app-bar`, `.workspace`, `.side-panel`, `.comic-stage`, `.scene-item`.
- Use state classes for client-managed state: `.is-active`, `.is-selected`, `.is-busy`.
- Use attribute selectors for hidden and data-driven states: `[hidden]`, `.comic-sheet[data-slot="main"]`, `.comic-sheet[data-slot="left"]`, `.comic-sheet[data-slot="right"]`.

**JavaScript Functions:**
- Use camelCase function names: `buildImagePrompt()`, `callOpenRouter()`, `generateComicPage()`, `renderScenes()`, `pushHistory()`, `setSideTab()`.
- In `scripts/creator.js`, pair setters/renderers with state they mutate: `setPage()`, `setStyle()`, `setTone()`, `setModel()`, `renderPageStrip()`, `renderScenes()`.
- In `server.js`, keep route handlers named after their route purpose: `handleHealth()`, `handleAiText()`, `generateComicPage()`, `serveStatic()`.

## Where to Add New Code

**New Static Landing Section:**
- Primary code: `index.html`
- Styles: `styles.css`
- Browser behavior: `scripts/main.js` only if the section needs interaction.
- Assets: `assets/`

**New Creator Workspace Control:**
- Markup: `create.html`
- Styles: `creator.css`
- Behavior/state: `scripts/creator.js`
- Use a stable ID for unique fields and `data-*` attributes for buttons, tabs, repeated items, and dynamic containers.

**New Creator State Field:**
- Primary code: `scripts/creator.js`
- Update `getSnapshot()` and `restoreSnapshot()` if the field participates in undo/redo.
- Update initialization near the bottom of `scripts/creator.js` if the field needs a default render pass.
- Add matching markup in `create.html` and styling in `creator.css`.

**New AI Text Task:**
- Server registry: `TEXT_TASKS` in `server.js`
- Server route: Reuse `POST /api/ai-text` through `handleAiText()` when the output is text-like.
- Client caller: `callAiText(task)` in `scripts/creator.js`
- UI trigger: Add a `data-*` action button in `create.html` and bind it in `scripts/creator.js`.

**New AI Image/Comic Operation:**
- Server API: Add a handler in `server.js` near `generateComicPage()` and wire it into the `http.createServer()` dispatcher.
- Prompt logic: Add a dedicated prompt builder in `server.js` instead of mixing unrelated prompt construction into `buildImagePrompt()`.
- Client API call: Add a focused function in `scripts/creator.js` near `generateComicPage()`.
- UI: Add controls in `create.html` and styles in `creator.css`.

**New Backend Runtime Module:**
- Current implementation is single-file `server.js`; for small endpoint additions, add helpers in `server.js` near related functions.
- For larger backend work, create a new server directory such as `backend/src/` or `server/` as part of that backend phase and migrate route, OpenRouter, config, and persistence code deliberately.
- Keep `backend/BACKEND_TZ.md` as requirements documentation, not runtime code.

**New API Endpoint:**
- Primary code: `server.js`
- Add JSON parsing with `readJson()` for POST/PUT-like routes.
- Respond with `sendJson()` for JSON APIs.
- Wire the route explicitly in the `http.createServer()` callback before the static file fallback.

**New Static Asset:**
- File location: `assets/`
- Reference from HTML/CSS/JS using relative paths like `assets/my-image.png`.
- Keep generated AI output out of `assets/` unless it is an intentional committed sample/reference asset.

**New Planning Document:**
- File location: `.planning/`
- Codebase intelligence location: `.planning/codebase/`
- Do not modify other mapper files unless that focus area is assigned.

**Utilities:**
- Browser-only helpers that are specific to the creator belong in `scripts/creator.js`.
- Landing-only helpers belong in `scripts/main.js`.
- Server-only helpers belong in `server.js`.
- Introduce shared files only when logic is reused across pages or server handlers; the current structure is page/file scoped.

## Special Directories

**`.planning/`:**
- Purpose: GSD planning state and generated analysis documents.
- Generated: Yes
- Committed: Project policy dependent; current mapper output is written here.

**`.planning/codebase/`:**
- Purpose: Codebase map documents consumed by GSD planning/execution commands.
- Generated: Yes
- Committed: Project policy dependent; do not overwrite documents outside the assigned focus.

**`assets/`:**
- Purpose: Runtime static images.
- Generated: No for current committed contents; generated AI images are returned as URLs/data URLs at runtime.
- Committed: Yes

**`backend/`:**
- Purpose: Backend requirements and design notes.
- Generated: No
- Committed: Yes

**`scripts/`:**
- Purpose: Runtime browser JavaScript.
- Generated: No
- Committed: Yes

**`.git/`:**
- Purpose: Git repository metadata.
- Generated: Yes
- Committed: No

**`node_modules/`:**
- Purpose: Dependency install directory if dependencies are added later.
- Generated: Yes
- Committed: No
- Current status: Not detected in project file listing.

---

*Structure analysis: 2026-04-25*
