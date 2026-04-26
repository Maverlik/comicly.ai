from httpx import AsyncClient

from app.core.errors import ApiError


async def test_health_returns_minimal_non_secret_payload(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    response_text = response.text.lower()
    forbidden_tokens = [
        "database_url",
        "api_key",
        "openrouter",
        "secret",
        "model",
    ]
    assert all(token not in response_text for token in forbidden_tokens)


async def test_ready_returns_ready_when_database_check_succeeds(
    async_client: AsyncClient,
    monkeypatch,
) -> None:
    async def check_database_ready() -> None:
        return None

    monkeypatch.setattr(
        "app.api.health.check_database_ready",
        check_database_ready,
    )

    response = await async_client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_ready_returns_database_unavailable_error_when_check_fails(
    async_client: AsyncClient,
    monkeypatch,
) -> None:
    async def check_database_ready() -> None:
        raise ApiError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="Database is not ready",
        )

    monkeypatch.setattr(
        "app.api.health.check_database_ready",
        check_database_ready,
    )

    response = await async_client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "DATABASE_UNAVAILABLE",
            "message": "Database is not ready",
        }
    }
