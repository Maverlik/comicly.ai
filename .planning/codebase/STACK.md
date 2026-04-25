# Technology Stack

**Analysis Date:** 2026-04-25

## Languages

**Primary:**
- JavaScript - Used for the Node server in `server.js` and browser behavior in `scripts/main.js` and `scripts/creator.js`.
- HTML - Static pages in `index.html` and `create.html`.
- CSS - Static styling in `styles.css` and `creator.css`.

**Secondary:**
- Markdown - Planning/backend requirements in `backend/BACKEND_TZ.md` and generated codebase intelligence in `.planning/codebase/`.

## Runtime

**Environment:**
- Node.js `>=22` - Declared in `package.json`; required because `server.js` uses native CommonJS modules and the global `fetch` API available in modern Node.
- Browser runtime - Vanilla DOM APIs drive the landing page carousel in `scripts/main.js` and the comic creator workspace in `scripts/creator.js`.

**Package Manager:**
- npm is implied by the `npm start` workflow and `package.json` scripts.
- Package manager version is not specified in `package.json`.
- Lockfile: missing. No `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, or `bun.lockb` detected.

## Frameworks

**Core:**
- Not detected. The server uses Node core modules only: `node:http`, `node:fs`, and `node:path` in `server.js`.
- Static frontend, no client framework. `index.html` loads `scripts/main.js`; `create.html` loads `scripts/creator.js`.

**Testing:**
- Not detected. No test framework dependency, test script, or test configuration is declared in `package.json`.

**Build/Dev:**
- No build step detected. Static files are served directly by `server.js`.
- `node server.js` - The only declared script in `package.json`, exposed as `npm start`.

## Key Dependencies

**Critical:**
- Node core `http` - HTTP server and route dispatch in `server.js`.
- Node core `fs` - Static file streaming and local `.env` parsing in `server.js`.
- Node core `path` - Filesystem path normalization and static asset lookup in `server.js`.
- Global `fetch` - Calls OpenRouter from `server.js`; requires a Node runtime that provides `fetch`.
- Browser DOM APIs - UI state, event handling, history, and workspace interactions in `scripts/creator.js`.

**Infrastructure:**
- No npm runtime dependencies are declared in `package.json`.
- No npm development dependencies are declared in `package.json`.
- Static image assets are stored in `assets/` and referenced by `index.html`, `create.html`, and `scripts/creator.js`.

## Configuration

**Environment:**
- `server.js` manually loads a root `.env` file before handling requests. The implementation parses simple `KEY=value` lines and only sets variables that are not already present in `process.env`.
- `.env.example` is present and should be treated as environment documentation; contents were not inspected because `.env*` files can contain secrets.
- Required for AI functionality: `OPENROUTER_API_KEY`.
- Optional runtime configuration used by `server.js`: `PORT`, `OPENROUTER_SITE_URL`, `OPENROUTER_APP_NAME`, `OPENROUTER_IMAGE_MODEL`, `OPENROUTER_IMAGE_ASPECT_RATIO`, and `OPENROUTER_TEXT_MODEL`.
- Default server port: `3000`, unless `PORT` is set.

**Build:**
- `package.json` - Defines project metadata, Node engine, and `start` script.
- No `tsconfig.json`, bundler config, lint config, or test config detected.
- No frontend build artifact directory is required; source HTML, CSS, JS, and assets are served directly.

## Platform Requirements

**Development:**
- Install/use Node.js `>=22`.
- Run `npm start` from the repository root to start `server.js`.
- Configure OpenRouter credentials through environment variables or the root `.env` file before using AI endpoints.
- Keep secrets out of browser code; `scripts/creator.js` calls same-origin endpoints and does not hold provider credentials.

**Production:**
- Deployment target is not implemented as code or config.
- `backend/BACKEND_TZ.md` documents Vercel or similar cloud hosting as an acceptable future target, but no `vercel.json`, CI config, database migration setup, or production deployment config is present.
- Production must provide env vars outside source control; `server.js` falls back to `.env` for local development.

---

*Stack analysis: 2026-04-25*
