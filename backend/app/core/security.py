from collections import defaultdict, deque
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.errors import ApiError, error_response

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def is_sensitive_path(path: str, method: str) -> bool:
    """Return true for routes that need MVP abuse throttling."""

    if path.startswith("/api/v1/auth/"):
        return True
    if path == "/api/v1/me/logout":
        return True
    if path == "/api/v1/me" and method in {"PATCH", "PUT"}:
        return True
    if path in {"/api/v1/ai-text", "/api/v1/generations"}:
        return True
    if path.startswith("/api/v1/comics") and method in WRITE_METHODS:
        return True
    if path == "/api/v1/payments" and method == "POST":
        return True
    if (
        path.startswith("/api/v1/payments/")
        and path.endswith("/refresh")
        and method == "POST"
    ):
        return True
    return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if not self.settings.security_headers_enabled:
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        if self.settings.is_production and self.settings.session_cookie_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.settings.rate_limit_enabled:
            return await call_next(request)

        if not is_sensitive_path(request.url.path, request.method.upper()):
            return await call_next(request)

        now = monotonic()
        key = self._client_key(request)
        bucket = self.requests[key]
        window_started = now - self.settings.rate_limit_window_seconds
        while bucket and bucket[0] <= window_started:
            bucket.popleft()

        if len(bucket) >= self.settings.rate_limit_max_requests:
            retry_after = self._retry_after(bucket, now)
            response = error_response(
                ApiError(
                    status_code=429,
                    code="RATE_LIMITED",
                    message="Too many requests. Please try again shortly.",
                )
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        bucket.append(now)
        return await call_next(request)

    def _client_key(self, request: Request) -> str:
        session_cookie = request.cookies.get(self.settings.session_cookie_name)
        if session_cookie:
            return f"session:{session_cookie}"

        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',', 1)[0].strip()}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    def _retry_after(self, bucket: deque[float], now: float) -> int:
        oldest = bucket[0] if bucket else now
        remaining = self.settings.rate_limit_window_seconds - int(now - oldest)
        return max(1, remaining)
