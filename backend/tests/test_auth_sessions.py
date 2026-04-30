from datetime import UTC, datetime

from fastapi import Response

from app.core.config import Settings
from app.services.auth_sessions import (
    build_product_session,
    clear_product_session_cookie,
    hash_session_token,
    set_product_session_cookie,
)


def test_product_session_uses_opaque_token_and_hash() -> None:
    settings = Settings(_env_file=None)

    first = build_product_session(settings)
    second = build_product_session(settings)

    assert first.raw_token != second.raw_token
    assert first.token_hash == hash_session_token(first.raw_token)
    assert first.token_hash != first.raw_token
    assert len(first.token_hash) == 64
    assert first.expires_at > datetime.now(UTC)


def test_product_session_cookie_uses_configured_flags() -> None:
    settings = Settings(
        _env_file=None,
        session_cookie_name="comicly_session",
        session_cookie_domain=".comicly-ai.ru",
        session_cookie_secure=True,
        session_cookie_samesite="lax",
        session_lifetime_days=30,
    )
    response = Response()

    set_product_session_cookie(response, token="raw-token", settings=settings)

    cookie = response.headers["set-cookie"]
    assert "comicly_session=raw-token" in cookie
    assert "Domain=.comicly-ai.ru" in cookie
    assert "HttpOnly" in cookie
    assert "Max-Age=2592000" in cookie
    assert "Path=/" in cookie
    assert "SameSite=lax" in cookie
    assert "Secure" in cookie


def test_clear_product_session_cookie_matches_cookie_scope() -> None:
    settings = Settings(
        _env_file=None,
        session_cookie_name="comicly_session",
        session_cookie_domain=".comicly-ai.ru",
        session_cookie_secure=True,
        session_cookie_samesite="lax",
    )
    response = Response()

    clear_product_session_cookie(response, settings=settings)

    cookie = response.headers["set-cookie"]
    assert "comicly_session=" in cookie
    assert "Domain=.comicly-ai.ru" in cookie
    assert "Max-Age=0" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Secure" in cookie
