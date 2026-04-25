# External Integrations

**Analysis Date:** 2026-04-25

## APIs & External Services

**AI Generation:**
- OpenRouter - Used by `server.js` to generate comic images and text through `POST https://openrouter.ai/api/v1/chat/completions`.
  - SDK/Client: native `fetch` in `server.js`; no OpenRouter npm SDK is installed.
  - Auth: `OPENROUTER_API_KEY`.
  - Request headers: `Authorization`, `Content-Type`, `HTTP-Referer`, and `X-Title` are set in `server.js`.
  - Optional identity/config headers use `OPENROUTER_SITE_URL` and `OPENROUTER_APP_NAME`.
  - Default image model in server code: `google/gemini-2.5-flash-image-preview`.
  - Default text model in server code: `google/gemini-2.5-flash`.
  - User-selectable image models allowed by `server.js`: `bytedance-seed/seedream-4.5`, `google/gemini-3-pro-image-preview`, and `openai/gpt-5.4-image-2`.

**Same-Origin Browser APIs:**
- `GET /api/health` - Used by `scripts/creator.js` to check whether the OpenRouter key is configured.
  - Implementation: `handleHealth` in `server.js`.
  - Auth: none.
- `POST /api/ai-text` - Used by `scripts/creator.js` for story enhancement, dialogue, captions, and scene suggestions.
  - Implementation: `handleAiText` in `server.js`.
  - Upstream: OpenRouter chat completions.
- `POST /api/generate-comic-page` - Used by `scripts/creator.js` for comic page generation.
  - Implementation: `generateComicPage` in `server.js`.
  - Upstream: OpenRouter chat completions with image modalities.

**Outbound Links:**
- OpenRouter key management link - `create.html` links to `https://openrouter.ai/keys` in the local configuration banner.

## Data Storage

**Databases:**
- Not detected in implemented code.
- `backend/BACKEND_TZ.md` documents future database-backed users, profiles, coin balances, transactions, payments, and comic history, but no database client, schema, migration tool, or connection code exists.
  - Connection: planned `DATABASE_URL` is listed in `backend/BACKEND_TZ.md`; not used by `server.js`.
  - Client: Not detected.

**File Storage:**
- Local filesystem only for committed static assets in `assets/`.
- `server.js` serves files from the repository root and streams assets via `fs.createReadStream`.
- Generated comic output is returned to the browser as an image URL or data URL and stored only in client-side in-memory arrays in `scripts/creator.js`.
- `backend/BACKEND_TZ.md` documents future avatar/object storage, but no storage provider integration is implemented.

**Caching:**
- None detected.
- JSON API responses in `server.js` explicitly set `Cache-Control: no-store`.
- Static file responses in `server.js` do not set explicit cache headers.

## Authentication & Identity

**Auth Provider:**
- Not implemented.
  - Implementation: demo-only profile UI is hardcoded in `create.html` and `scripts/creator.js`.
  - `server.js` does not implement sessions, cookies, login, logout, JWT, OAuth, or protected routes.
  - `backend/BACKEND_TZ.md` documents future Google and Yandex OAuth with server-side sessions, but those integrations are requirements only.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- `server.js` logs the startup URL with `console.log`.
- API errors are returned as JSON responses from `server.js`.
- No structured logger, request logger, tracing, metrics, or external observability service is configured.

## CI/CD & Deployment

**Hosting:**
- Not configured in code.
- `backend/BACKEND_TZ.md` allows Vercel or similar hosting as a future deployment target, but no deployment config is present.

**CI Pipeline:**
- None detected. No GitHub Actions, Vercel config, or other CI/CD workflow files were found in the explored project surface.

## Environment Configuration

**Required env vars:**
- `OPENROUTER_API_KEY` - Required by `server.js` for all OpenRouter-backed AI operations.

**Optional env vars used by implemented code:**
- `PORT` - Server listen port in `server.js`; defaults to `3000`.
- `OPENROUTER_SITE_URL` - Sent as the OpenRouter `HTTP-Referer` header by `server.js`; defaults to `http://localhost:3000`.
- `OPENROUTER_APP_NAME` - Sent as the OpenRouter `X-Title` header by `server.js`; defaults to `comicly.ai`.
- `OPENROUTER_IMAGE_MODEL` - Server-side fallback image model in `server.js`.
- `OPENROUTER_IMAGE_ASPECT_RATIO` - Image generation aspect ratio in `server.js`; defaults to `1:1`.
- `OPENROUTER_TEXT_MODEL` - Server-side text model in `server.js`.

**Planned env vars documented but not implemented:**
- `DATABASE_URL`, `SESSION_SECRET`, `APP_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`, object storage variables, and `STARTER_COINS` are listed in `backend/BACKEND_TZ.md`.

**Secrets location:**
- `.env.example` is present as an example/configuration file.
- Runtime secrets should be provided through process environment or local `.env`; `server.js` reads root `.env` if present.
- Secret values were not read or quoted.

## Webhooks & Callbacks

**Incoming:**
- None implemented.
- No webhook routes exist in `server.js`.
- `backend/BACKEND_TZ.md` references future payment-provider readiness, but payment webhooks are explicitly outside the current documented task unless separately agreed.

**Outgoing:**
- OpenRouter API calls from `server.js` to `https://openrouter.ai/api/v1/chat/completions`.
- No other outbound service calls detected in implemented code.

---

*Integration audit: 2026-04-25*
