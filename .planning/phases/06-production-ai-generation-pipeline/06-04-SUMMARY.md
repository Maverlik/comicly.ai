# Plan 06-04 Summary

Status: complete

Implemented:
- Added authenticated `POST /api/v1/generations` with `Idempotency-Key`, creator-compatible payload aliases, job/page/balance response shape, and small URL-only image output.
- Added authenticated `POST /api/v1/ai-text` with fakeable OpenRouter text dependency and optional parsed `scenes` output.
- Registered both routers under `/api/v1`.
- Added API tests for auth, idempotency requirement, model rejection, success response shape, provider failure, AI text behavior, and wallet/job non-mutation for text assistance.

Verification:
- `python -m pytest tests/test_generations_api.py tests/test_ai_text_api.py tests/test_generation_service.py`
- `python -m ruff check app/api/v1/generations.py app/api/v1/ai_text.py app/api/v1/__init__.py tests/test_generations_api.py tests/test_ai_text_api.py`
- `python -m ruff format --check app/api/v1/generations.py app/api/v1/ai_text.py app/api/v1/__init__.py tests/test_generations_api.py tests/test_ai_text_api.py`
