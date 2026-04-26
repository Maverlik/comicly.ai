from fastapi import Query
from httpx import ASGITransport, AsyncClient

from app.core.errors import ApiError, error_response
from app.main import create_app


def test_api_error_response_uses_machine_readable_error_envelope() -> None:
    response = error_response(
        ApiError(
            status_code=409,
            code="INSUFFICIENT_COINS",
            message="Not enough coins.",
        )
    )

    assert response.status_code == 409
    assert response.body == (
        b'{"error":{"code":"INSUFFICIENT_COINS","message":"Not enough coins."}}'
    )


async def test_validation_error_uses_stable_error_envelope() -> None:
    app = create_app()

    @app.get("/probe-validation")
    async def probe_validation(count: int = Query(...)) -> dict[str, int]:
        return {"count": count}

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/probe-validation",
            params={"count": "not-an-int"},
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid request.",
        }
    }
