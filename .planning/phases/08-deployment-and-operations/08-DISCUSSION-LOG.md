# Phase 8: Deployment And Operations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-29
**Phase:** 8 - Deployment And Operations
**Areas discussed:** deployment execution, project shape, secrets/env policy, production smoke scope, security/ops minimum

---

## Deployment Execution

| Option | Description | Selected |
| --- | --- | --- |
| A | Codex prepares config/docs, tries real Vercel setup/deploy through available tools, and records exact manual checklist if access/secrets block automation. | yes |
| B | Only config/docs, no real deploy attempt. | |
| C | Only local/dev readiness, production deploy later. | |

**User's choice:** A, via "Все A".
**Notes:** This follows the earlier preference that deployment should use the path Codex can configure most independently.

---

## Vercel Project Shape

| Option | Description | Selected |
| --- | --- | --- |
| A | Two Vercel projects from one repo: root frontend for `comicly.ai`/`www`, backend project rooted at `backend/` for `api.comicly.ai`. | yes |
| B | One Vercel project through Services/monorepo approach. | |
| C | Frontend on Vercel, backend prepared immediately for Render/Railway fallback. | |

**User's choice:** A, via "Все A".
**Notes:** This preserves the already-decided separate API-only backend shape and avoids depending on Vercel Services for MVP stability.

---

## Secrets And Environment Policy

| Option | Description | Selected |
| --- | --- | --- |
| A | Never commit real secrets; update `.env.example`, docs, and Vercel env checklist; use Vercel env/marketplace values for deploy. | yes |
| B | Also create local helper scripts for env push/check. | |
| C | Documentation only, without attempting env setup in Vercel. | |

**User's choice:** A, via "Все A".
**Notes:** Production secrets include Neon, OAuth providers, OpenRouter, Vercel Blob, cookie/session settings, and CORS origins.

---

## Production Smoke Scope

| Option | Description | Selected |
| --- | --- | --- |
| A | Smoke checks public reachability, `/health`, `/ready`, creator auth entry/login links, and CORS/cookie shape; live OAuth/generation only when secrets are configured. | yes |
| B | Require live Google/Yandex OAuth and live generation to pass in Phase 8. | |
| C | Production smoke remains manual-only. | |

**User's choice:** A, via "Все A".
**Notes:** Provider-secret-dependent checks must be explicit manual gates if credentials/domains are not available during execution.

---

## Security And Operations Minimum

| Option | Description | Selected |
| --- | --- | --- |
| A | Add backend security headers plus simple portable in-process rate limiting for sensitive endpoints. | yes |
| B | Use Vercel Firewall/platform rate limiting as the primary mechanism. | |
| C | Only document rate limiting; implement later. | |

**User's choice:** A, via "Все A".
**Notes:** Rate limiting should protect auth/profile writes/AI/generation without requiring Redis or a platform-specific service in the MVP.

---

## the agent's Discretion

- Exact Vercel config file shape.
- Exact docs layout and deploy command checklist.
- Exact MVP rate-limit thresholds.
- Exact production smoke implementation, as long as automated vs manual/provider-secret-dependent checks are clearly separated.

## Deferred Ideas

- Async generation worker/queue/polling flow.
- Vercel Firewall as a required production dependency.
- Full external observability stack.
- Payment checkout/webhook operations.
