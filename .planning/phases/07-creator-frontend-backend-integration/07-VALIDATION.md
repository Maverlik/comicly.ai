# Phase 7 Validation Strategy

## Validation Architecture

Phase 7 needs both contract-level and browser-level validation because it changes static frontend behavior against the FastAPI backend.

## Required Checks

1. Backend regression gate:
   - `cd backend; python -m pytest`
   - `cd backend; python -m ruff check .`
   - `cd backend; python -m ruff format --check .`

2. Static/root contract gate:
   - Root tests or equivalent assertions must verify landing remains public and creator contains the auth gate/contracts.
   - No secret values or OpenRouter keys are exposed in frontend files.

3. Browser smoke gate:
   - Open landing page and confirm it remains public.
   - Open creator without session and confirm login overlay appears.
   - With authenticated local/session setup, confirm profile/balance render from backend.
   - Trigger generation through frontend with a fake or controlled backend response where practical.
   - Confirm success updates image and balance.
   - Confirm insufficient coins and generation failure are visible recoverable errors.
   - Confirm logout returns to auth overlay.

## Notes

Live OAuth provider login may require manual/provider credentials. Automated smoke can verify login link targets and session bootstrap behavior with a seeded local session.
