import pytest
from fastapi import Query
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.errors import ApiError, error_response
from app.main import app, create_app


def test_create_app_returns_fastapi_instance():
    created_app = create_app()

    assert created_app.title
    assert app.title


def test_settings_load_safe_defaults_without_future_secrets():
    settings = Settings()

    assert settings.app_name
    assert settings.app_env
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_api_error_response_uses_stable_envelope():
    response = error_response(
        ApiError(503, "DATABASE_UNAVAILABLE", "Database is not ready")
    )

    assert response.status_code == 503
    assert response.body == (
        b'{"error":{"code":"DATABASE_UNAVAILABLE","message":"Database is not ready"}}'
    )


@pytest.mark.asyncio
async def test_validation_errors_use_stable_envelope_without_request_details():
    test_app = create_app()

    @test_app.get("/probe")
    async def probe(count: int = Query(...)):
        return {"count": count}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/probe", params={"count": "not-an-int"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid request.",
        }
    }
