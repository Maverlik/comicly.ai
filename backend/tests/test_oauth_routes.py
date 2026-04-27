from collections.abc import AsyncIterator

import pytest
from fastapi.responses import RedirectResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.v1.auth import (
    get_oauth_provider_service,
)
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.user import UserSession
from app.services.oauth_providers import (
    OAuthProfile,
    OAuthProviderError,
    normalize_google_profile,
    normalize_yandex_profile,
)


@pytest.fixture
async def session_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


class FakeOAuthProviderService:
    def __init__(self, profile: OAuthProfile | None = None, should_fail: bool = False):
        self.profile = profile or OAuthProfile(
            provider="google",
            provider_user_id="google-1",
            email="user@example.com",
            email_verified=True,
            display_name="User One",
            avatar_url="https://example.com/avatar.png",
        )
        self.should_fail = should_fail
        self.redirect_uri = None

    async def authorize_redirect(self, *, provider, request, redirect_uri):
        self.redirect_uri = redirect_uri
        return RedirectResponse(f"https://oauth.example/{provider}", status_code=302)

    async def authorize_callback(self, *, provider, request):
        if self.should_fail:
            raise OAuthProviderError("OAUTH_FAILED")
        return self.profile


async def test_google_login_starts_backend_owned_redirect() -> None:
    app = create_app()
    fake_provider = FakeOAuthProviderService()
    app.dependency_overrides[get_oauth_provider_service] = lambda: fake_provider

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
    ) as client:
        response = await client.get("/api/v1/auth/google/login")

    assert response.status_code == 302
    assert response.headers["location"] == "https://oauth.example/google"
    assert fake_provider.redirect_uri == (
        "http://testserver/api/v1/auth/google/callback"
    )


async def test_unknown_provider_returns_stable_error(async_client) -> None:
    response = await async_client.get("/api/v1/auth/github/login")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OAUTH_PROVIDER_UNSUPPORTED"


async def test_oauth_callback_bootstraps_user_and_sets_product_session_cookie(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app()
    fake_provider = FakeOAuthProviderService()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_oauth_provider_service] = lambda: fake_provider

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
    ) as client:
        response = await client.get("/api/v1/auth/google/callback")

    assert response.status_code == 303
    assert response.headers["location"] == "https://comicly.ai/create.html"
    cookie = response.headers["set-cookie"]
    assert "comicly_session=" in cookie
    assert "HttpOnly" in cookie

    async with session_maker() as session:
        db_sessions = (await session.execute(select(UserSession))).scalars().all()

    assert len(db_sessions) == 1
    assert "comicly_session=" + db_sessions[0].session_token_hash not in cookie


async def test_oauth_callback_redirects_stable_error_on_provider_failure(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_oauth_provider_service] = (
        lambda: FakeOAuthProviderService(should_fail=True)
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
    ) as client:
        response = await client.get("/api/v1/auth/google/callback")

    assert response.status_code == 303
    assert response.headers["location"] == (
        "https://comicly.ai/create.html?auth_error=oauth_failed"
    )


def test_provider_profile_normalization() -> None:
    google = normalize_google_profile(
        {
            "sub": "google-1",
            "email": "user@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "https://example.com/google.png",
        }
    )
    yandex = normalize_yandex_profile(
        {
            "id": "yandex-1",
            "default_email": "user@example.com",
            "is_verified": True,
            "real_name": "Yandex User",
            "default_avatar_id": "avatar-id",
        }
    )

    assert google.provider == "google"
    assert google.email_verified is True
    assert google.avatar_url == "https://example.com/google.png"
    assert yandex.provider == "yandex"
    assert yandex.email_verified is True
    assert yandex.avatar_url == (
        "https://avatars.yandex.net/get-yapic/avatar-id/islands-200"
    )
