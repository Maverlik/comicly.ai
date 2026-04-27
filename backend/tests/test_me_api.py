from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.user import User, UserProfile, UserSession
from app.models.wallet import Wallet
from app.services.auth_sessions import hash_session_token


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


async def seed_authenticated_user(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    token: str = "valid-token",
) -> User:
    async with session_maker() as session:
        user = User(
            email="user@example.com",
            display_name="Original Name",
            avatar_url="https://example.com/avatar.png",
        )
        session.add(user)
        await session.flush()
        session.add(UserProfile(user_id=user.id, username="comic_user", bio="Bio"))
        session.add(Wallet(user_id=user.id, balance=100))
        session.add(
            UserSession(
                user_id=user.id,
                session_token_hash=hash_session_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        await session.commit()
        return user


@pytest.fixture
async def app_client(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


async def test_get_me_requires_authentication(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_get_me_returns_account_profile_and_wallet_summary(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_authenticated_user(session_maker)

    response = await app_client.get(
        "/api/v1/me",
        cookies={"comicly_session": "valid-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["account"] == {
        "id": str(user.id),
        "email": "user@example.com",
        "display_name": "Original Name",
        "avatar_url": "https://example.com/avatar.png",
    }
    assert payload["profile"] == {"username": "comic_user", "bio": "Bio"}
    assert payload["wallet"] == {"balance": 100}


async def test_update_display_name_persists_and_returns_updated_me(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_authenticated_user(session_maker)

    response = await app_client.patch(
        "/api/v1/me",
        json={"display_name": "New Name"},
        cookies={"comicly_session": "valid-token"},
    )

    async with session_maker() as session:
        db_user = (
            await session.execute(select(User).where(User.id == user.id))
        ).scalar_one()

    assert response.status_code == 200
    assert response.json()["account"]["display_name"] == "New Name"
    assert db_user.display_name == "New Name"


async def test_logout_revokes_current_session_and_clears_cookie(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await seed_authenticated_user(session_maker)

    response = await app_client.post(
        "/api/v1/me/logout",
        cookies={"comicly_session": "valid-token"},
    )

    async with session_maker() as session:
        db_session = (await session.execute(select(UserSession))).scalar_one()

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert db_session.revoked_at is not None
    assert "comicly_session=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
