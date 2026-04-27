from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.errors import ApiError, error_response
from app.db.base import Base
from app.db.session import get_async_session
from app.models.user import User, UserSession
from app.services.auth_sessions import hash_session_token
from app.services.current_user import CurrentUserContext, get_current_user

CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]


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


@pytest.fixture
async def current_user_app(
    session_maker: async_sessionmaker[AsyncSession],
) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(ApiError)
    async def api_error_handler(_request, exc: ApiError):
        return error_response(exc)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session

    @app.get("/private")
    async def private_route(
        current_user: CurrentUserDep,
    ):
        return {"user_id": str(current_user.user.id)}

    return app


async def create_session_row(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    token: str = "raw-token",
    email: str = "user@example.com",
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> User:
    async with session_maker() as session:
        user = User(email=email, display_name="User", avatar_url=None)
        session.add(user)
        await session.flush()
        session.add(
            UserSession(
                user_id=user.id,
                session_token_hash=hash_session_token(token),
                expires_at=expires_at or datetime.now(UTC) + timedelta(days=1),
                revoked_at=revoked_at,
            )
        )
        await session.commit()
        return user


async def test_missing_cookie_returns_auth_required(current_user_app: FastAPI) -> None:
    transport = ASGITransport(app=current_user_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/private")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_unknown_session_token_returns_stable_error(
    current_user_app: FastAPI,
) -> None:
    transport = ASGITransport(app=current_user_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/private",
            cookies={"comicly_session": "unknown"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_INVALID"


async def test_expired_and_revoked_sessions_are_rejected(
    current_user_app: FastAPI,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await create_session_row(
        session_maker,
        token="expired-token",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    await create_session_row(
        session_maker,
        token="revoked-token",
        email="revoked@example.com",
        revoked_at=datetime.now(UTC),
    )

    transport = ASGITransport(app=current_user_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        expired = await client.get(
            "/private",
            cookies={"comicly_session": "expired-token"},
        )
        revoked = await client.get(
            "/private",
            cookies={"comicly_session": "revoked-token"},
        )

    assert expired.status_code == 401
    assert expired.json()["error"]["code"] == "SESSION_EXPIRED"
    assert revoked.status_code == 401
    assert revoked.json()["error"]["code"] == "SESSION_REVOKED"


async def test_valid_session_resolves_trusted_db_user(
    current_user_app: FastAPI,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_session_row(session_maker, token="valid-token")

    transport = ASGITransport(app=current_user_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/private",
            cookies={"comicly_session": "valid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"user_id": str(user.id)}
