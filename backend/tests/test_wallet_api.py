from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.user import User, UserSession
from app.models.wallet import Wallet
from app.services.auth_sessions import hash_session_token
from app.services.wallets import GenerationCostKind, debit_generation_cost, grant_coins


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


async def seed_authenticated_user(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    token: str = "valid-token",
    balance: int = 100,
) -> User:
    async with session_maker() as session:
        user = User(email="user@example.com", display_name="User")
        session.add(user)
        await session.flush()
        session.add(Wallet(user_id=user.id, balance=balance))
        session.add(
            UserSession(
                user_id=user.id,
                session_token_hash=hash_session_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        await session.commit()
        return user


async def test_get_wallet_requires_authentication(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/v1/wallet")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_get_wallet_returns_balance_and_recent_transactions(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_authenticated_user(session_maker, balance=50)

    async with session_maker() as session:
        await grant_coins(
            session,
            user_id=user.id,
            amount=10,
            reference_type="test",
            reference_id=user.id,
            idempotency_key="api-grant",
        )
        await debit_generation_cost(
            session,
            user_id=user.id,
            settings=Settings(_env_file=None, full_page_generation_cost=20),
            kind=GenerationCostKind.FULL_PAGE,
            reference_type="generation_job",
            reference_id=user.id,
            idempotency_key="api-debit",
        )
        await session.commit()

    response = await app_client.get(
        "/api/v1/wallet",
        cookies={"comicly_session": "valid-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["balance"] == 40
    amounts = [transaction["amount"] for transaction in payload["recent_transactions"]]
    assert amounts == [
        -20,
        10,
    ]
    assert payload["recent_transactions"][0]["reason"] == "generation_debit"
    assert "idempotency_key" not in payload["recent_transactions"][0]


async def test_duplicate_wallet_operation_is_not_duplicated_in_api_history(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_authenticated_user(session_maker, balance=50)

    async with session_maker() as session:
        for _ in range(2):
            await debit_generation_cost(
                session,
                user_id=user.id,
                settings=Settings(_env_file=None, full_page_generation_cost=20),
                kind=GenerationCostKind.FULL_PAGE,
                reference_type="generation_job",
                reference_id=user.id,
                idempotency_key="same-api-debit",
            )
        await session.commit()

    response = await app_client.get(
        "/api/v1/wallet",
        cookies={"comicly_session": "valid-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["balance"] == 30
    assert len(payload["recent_transactions"]) == 1
