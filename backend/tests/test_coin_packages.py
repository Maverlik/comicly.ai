from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.payment import CoinPackage
from app.services.coin_packages import (
    list_active_coin_packages,
    seed_default_coin_packages,
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


async def test_seed_default_coin_packages_is_idempotent(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    async with session_maker() as session:
        first = await seed_default_coin_packages(session)
        await session.commit()

        second = await seed_default_coin_packages(session)
        await session.commit()

        active_packages = await list_active_coin_packages(session)

    assert [package.code for package in first] == [
        "coins_100",
        "coins_500",
        "coins_1000",
    ]
    assert [package.code for package in second] == [
        "coins_100",
        "coins_500",
        "coins_1000",
    ]
    assert len(active_packages) == 3
    assert [package.coin_amount for package in active_packages] == [100, 500, 1000]


async def test_coin_package_catalog_returns_only_active_packages(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    async with session_maker() as setup_session:
        await seed_default_coin_packages(setup_session)
        setup_session.add(
            CoinPackage(
                code="inactive_test",
                name="Inactive test package",
                coin_amount=1,
                amount="0.01",
                currency="USD",
                active=False,
                sort_order=1,
            )
        )
        await setup_session.commit()

    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/coin-packages")

    assert response.status_code == 200
    payload = response.json()
    assert [item["code"] for item in payload] == [
        "coins_100",
        "coins_500",
        "coins_1000",
    ]
    assert [item["coin_amount"] for item in payload] == [100, 500, 1000]
    assert all(item["active"] is True for item in payload)
