from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.v1.ai_text import get_text_service
from app.core.errors import ApiError
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.generation import GenerationJob
from app.models.user import User, UserSession
from app.models.wallet import WalletTransaction
from app.services.auth_sessions import hash_session_token
from app.services.openrouter import OpenRouterTextResult


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


class FakeTextService:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.calls: list[dict] = []

    async def generate_text(self, *, task, payload, model=None):
        self.calls.append({"task": task, "payload": payload, "model": model})
        if self.error is not None:
            raise self.error
        text = (
            '["Panel one", "Panel two"]' if task == "scenes" else "Improved comic text."
        )
        return OpenRouterTextResult(
            text=text,
            model=model or "google/gemini-2.5-flash",
            response_payload={"ok": True},
        )


@pytest.fixture
async def app_client(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_text_service] = lambda: FakeTextService()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def seed_authenticated_user(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    token: str = "valid-token",
) -> User:
    async with session_maker() as session:
        user = User(email="user@example.com", display_name="User")
        session.add(user)
        await session.flush()
        session.add(
            UserSession(
                user_id=user.id,
                session_token_hash=hash_session_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        await session.commit()
        return user


def auth_header(token: str = "valid-token") -> dict[str, str]:
    return {"Cookie": f"comicly_session={token}"}


async def test_ai_text_requires_authentication(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/api/v1/ai-text",
        json={"task": "enhance", "story": "Story"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_ai_text_returns_text_and_keeps_generation_tables_empty(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await seed_authenticated_user(session_maker)

    response = await app_client.post(
        "/api/v1/ai-text",
        json={
            "task": "enhance",
            "story": "Story",
            "model_id": "text/model",
            "selectedScene": "Launch",
        },
        headers=auth_header(),
    )

    async with session_maker() as session:
        job_count = await session.scalar(
            select(func.count()).select_from(GenerationJob)
        )
        tx_count = await session.scalar(
            select(func.count()).select_from(WalletTransaction)
        )

    assert response.status_code == 200
    assert response.json() == {
        "text": "Improved comic text.",
        "model": "text/model",
        "scenes": None,
    }
    assert job_count == 0
    assert tx_count == 0


async def test_ai_text_scenes_parses_json_array(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await seed_authenticated_user(session_maker)

    response = await app_client.post(
        "/api/v1/ai-text",
        json={"task": "scenes", "story": "Story"},
        headers=auth_header(),
    )

    assert response.status_code == 200
    assert response.json()["scenes"] == ["Panel one", "Panel two"]


async def test_ai_text_provider_errors_are_typed(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_text_service] = lambda: FakeTextService(
        ApiError(502, "OPENROUTER_ERROR", "OpenRouter returned an error.")
    )
    await seed_authenticated_user(session_maker)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ai-text",
            json={"task": "enhance", "story": "Story"},
            headers=auth_header(),
        )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "OPENROUTER_ERROR"
