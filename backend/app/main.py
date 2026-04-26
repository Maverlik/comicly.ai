from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.api import health, v1
from app.core.config import get_settings
from app.core.errors import ApiError, error_response


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.app_debug)
    app.state.settings = settings

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError):
        return error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, _exc: RequestValidationError):
        return error_response(
            ApiError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Invalid request.",
            )
        )

    app.include_router(health.router)
    app.include_router(v1.router)

    return app


app = create_app()
