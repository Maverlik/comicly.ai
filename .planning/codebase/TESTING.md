# Testing Patterns

**Analysis Date:** 2026-04-25

## Test Framework

**Runner:**
- Not detected. There is no configured test runner in `package.json`.
- No `jest.config.*`, `vitest.config.*`, `playwright.config.*`, or equivalent test config files are present.

**Assertion Library:**
- Not detected. `package.json` has no dependencies or devDependencies.

**Run Commands:**
```bash
npm start              # Starts the local Node server from `server.js`
# Not detected         # Run all tests
# Not detected         # Watch mode
# Not detected         # Coverage
```

## Test File Organization

**Location:**
- Not detected. No `*.test.*` or `*.spec.*` files are present.
- Source files are organized as runtime files rather than testable modules: `server.js`, `scripts/main.js`, `scripts/creator.js`, `index.html`, `create.html`, `styles.css`, and `creator.css`.

**Naming:**
- Not detected for tests.
- Use the source filename plus `.test.js` if tests are introduced near the relevant file, such as `server.test.js` for `server.js` and `scripts/creator.test.js` for `scripts/creator.js`.

**Structure:**
```text
comicly.ai/
├── server.js              # Node HTTP server and API handlers
├── scripts/
│   ├── main.js            # Landing carousel behavior
│   └── creator.js         # Creator workspace behavior
├── index.html             # Landing page
├── create.html            # Creator app shell
├── styles.css             # Landing styles
└── creator.css            # Creator styles
```

## Test Structure

**Suite Organization:**
```javascript
// Not detected in repository.
// Match source boundaries when adding tests:
// describe("readJson", ...)
// describe("generateComicPage", ...)
// describe("creator workspace state", ...)
```

**Patterns:**
- Not detected for automated setup or teardown.
- Manual verification is the only available testing path. Use `npm start` from `package.json`, open `index.html` and `create.html` through the local server, and exercise UI flows against `server.js`.
- Server behavior can be checked through HTTP requests to `GET /api/health`, `POST /api/ai-text`, and `POST /api/generate-comic-page` in `server.js`.
- Browser behavior should verify DOM state changes driven by `data-*` selectors in `create.html` and `scripts/creator.js`.

## Mocking

**Framework:** Not detected

**Patterns:**
```javascript
// Not detected in repository.
// The code currently uses direct globals:
// - `fetch` in `server.js` and `scripts/creator.js`
// - `document`, `navigator`, and `window` in `scripts/creator.js`
// - Node `http`, `fs`, and `path` in `server.js`
```

**What to Mock:**
- Mock `fetch` for OpenRouter requests made by `callOpenRouter` in `server.js`.
- Mock browser `fetch` for `/api/ai-text`, `/api/generate-comic-page`, and `/api/health` requests in `scripts/creator.js`.
- Mock `navigator.share` and `navigator.clipboard.writeText` for `shareProject` in `scripts/creator.js`.
- Mock timers used by `showToast`, input history debounce timers, and carousel switching in `scripts/creator.js` and `scripts/main.js`.
- Use DOM fixtures based on `create.html` for selector-driven UI tests in `scripts/creator.js`.

**What NOT to Mock:**
- Do not mock pure transformation helpers such as `escapeHtml`, `getSnapshot`, `buildScenePayload`, `normalizeIndex`, and `slotForPage`; test their returned values directly.
- Do not mock local static asset paths when verifying generated DOM strings; assert the relative paths used in `scripts/creator.js`.

## Fixtures and Factories

**Test Data:**
```javascript
// Existing runtime fixtures in `scripts/creator.js`:
const pages = [createPlaceholderDataUrl(1), createPlaceholderDataUrl(2)];
const pageImages = [
  "assets/comic-preview-fantasy.png",
  "assets/comic-preview-japan.png",
];
const scenes = [];
```

**Location:**
- No dedicated test fixture directory is present.
- Runtime demo data lives directly in `scripts/creator.js` and `create.html`.
- Static visual fixtures live in `assets/`, including `assets/comic-preview-fantasy.png`, `assets/comic-preview-japan.png`, `assets/comic-preview-action.png`, and `assets/comicly-reference.png`.

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
# Not detected
```

## Test Types

**Unit Tests:**
- Not used.
- Best unit-test candidates are pure helpers in `server.js`: `buildImagePrompt`, `extractImageUrl`, `extractText`, and `normalizeTextTone`.
- Best unit-test candidates in `scripts/main.js` are `normalizeIndex` and `slotForPage`.
- Best unit-test candidates in `scripts/creator.js` are `escapeHtml`, `getSnapshot`, `buildScenePayload`, `setZoom`, and state setters that can run against a DOM fixture.

**Integration Tests:**
- Not used.
- API integration tests should cover `GET /api/health`, invalid JSON handling in `readJson`, missing `story` validation, missing `OPENROUTER_API_KEY` behavior, OpenRouter non-OK responses, and successful JSON response shapes in `server.js`.
- Browser integration tests should load `create.html`, execute `scripts/creator.js`, and verify tab switching, scene creation, history undo/redo, loading state, and error toast behavior.

**E2E Tests:**
- Not used.
- E2E coverage should start the app with `npm start`, visit `/`, verify carousel controls from `index.html` and `scripts/main.js`, visit `/create.html`, and verify creator actions wired through `create.html` and `scripts/creator.js`.

## Common Patterns

**Async Testing:**
```javascript
// Pattern to apply for server and browser async functions:
// 1. Arrange a mocked `fetch` response.
// 2. Await the function under test.
// 3. Assert response payload, UI state, or toast text.
```

**Error Testing:**
```javascript
// Pattern to apply for API and UI errors:
// - For `server.js`, assert HTTP status and JSON `{ error, code }`.
// - For `scripts/creator.js`, assert `showToast(error.message)` side effects.
// - For `MISSING_KEY`, assert `showConfigBanner()` reveals `[data-config-banner]`.
```

**Manual Smoke Checks:**
- Start the server with `npm start` from `package.json`.
- Visit `/api/health` and verify JSON includes `ok`, `hasApiKey`, `imageModel`, and `textModel` from `server.js`.
- Visit `/` and click carousel controls wired through `data-carousel-prev`, `data-carousel-next`, and `data-carousel-card` in `index.html` and `scripts/main.js`.
- Visit `/create.html` and check story counter, tabs, style/model selection, add scene, add page, undo/redo, zoom, download, share fallback, and config banner behavior wired through `create.html` and `scripts/creator.js`.

---

*Testing analysis: 2026-04-25*
