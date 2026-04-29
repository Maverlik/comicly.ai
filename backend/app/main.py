from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import health, v1
from app.core.config import Settings, get_settings
from app.core.errors import ApiError, error_response
from app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware

try:
    from starlette.middleware.sessions import SessionMiddleware
except ModuleNotFoundError:  # pragma: no cover - runtime requirements install this.

    class SessionMiddleware(BaseHTTPMiddleware):
        """Import-time fallback for environments missing Starlette's optional extra."""

        fallback_insecure = True

        def __init__(
            self,
            app,
            *,
            secret_key: str,
            session_cookie: str,
            max_age: int,
            same_site: str,
            https_only: bool,
        ) -> None:
            super().__init__(app)
            self.secret_key = secret_key
            self.session_cookie = session_cookie
            self.max_age = max_age
            self.same_site = same_site
            self.https_only = https_only

        async def dispatch(self, request: Request, call_next):
            request.scope.setdefault("session", {})
            return await call_next(request)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.app_debug)
    app.state.settings = settings

    cors_origins = settings.cors_origin_list
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if settings.is_production and getattr(
        SessionMiddleware, "fallback_insecure", False
    ):
        raise RuntimeError(
            "itsdangerous is required for production OAuth state cookies"
        )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.session_cookie_secure,
        same_site=settings.session_cookie_samesite,
        session_cookie="comicly_oauth_state",
        max_age=600,
    )
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)

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
