import pytest
from httpx import ASGITransport, AsyncClient

import app.main as app_main
from app.core.config import Settings
from app.main import create_app


async def client_for(settings: Settings) -> AsyncClient:
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.asyncio
async def test_security_headers_are_added_to_api_responses() -> None:
    async with await client_for(Settings()) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "camera=()" in response.headers["Permissions-Policy"]
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_hsts_is_added_only_for_secure_production() -> None:
    settings = Settings(
        app_env="production",
        session_secret="test-secret-not-default",
        session_cookie_secure=True,
    )
    if getattr(app_main.SessionMiddleware, "fallback_insecure", False):
        app_main.SessionMiddleware.fallback_insecure = False

    async with await client_for(settings) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")


@pytest.mark.asyncio
async def test_sensitive_routes_are_rate_limited_with_stable_error() -> None:
    settings = Settings(rate_limit_max_requests=2, rate_limit_window_seconds=60)

    async with await client_for(settings) as client:
        first = await client.post(
            "/api/v1/ai-text",
            json={"task": "enhance", "text": "hello"},
        )
        second = await client.post(
            "/api/v1/ai-text",
            json={"task": "enhance", "text": "hello"},
        )
        third = await client.post(
            "/api/v1/ai-text",
            json={"task": "enhance", "text": "hello"},
        )

    assert first.status_code != 429
    assert second.status_code != 429
    assert third.status_code == 429
    assert third.json() == {
        "error": {
            "code": "RATE_LIMITED",
            "message": "Too many requests. Please try again shortly.",
        }
    }
    assert int(third.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_health_and_ready_are_not_rate_limited() -> None:
    settings = Settings(rate_limit_max_requests=1, rate_limit_window_seconds=60)

    async with await client_for(settings) as client:
        responses = [await client.get("/health") for _ in range(3)]

    assert [response.status_code for response in responses] == [200, 200, 200]


@pytest.mark.asyncio
async def test_rate_limit_can_be_disabled() -> None:
    settings = Settings(rate_limit_enabled=False, rate_limit_max_requests=1)

    async with await client_for(settings) as client:
        responses = [
            await client.post(
                "/api/v1/ai-text",
                json={"task": "enhance", "text": "hello"},
            )
            for _ in range(3)
        ]

    assert all(response.status_code != 429 for response in responses)
