from collections.abc import AsyncIterator
from decimal import Decimal

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
        "coins_rub_450",
        "coins_rub_1200",
        "coins_rub_2600",
    ]
    assert [package.code for package in second] == [
        "coins_rub_450",
        "coins_rub_1200",
        "coins_rub_2600",
    ]
    assert len(active_packages) == 3
    assert [package.coin_amount for package in active_packages] == [450, 1200, 2600]


async def test_seed_default_coin_packages_deactivates_legacy_defaults(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    async with session_maker() as session:
        session.add_all(
            [
                CoinPackage(
                    code="coins_100",
                    name="100 coins",
                    coin_amount=100,
                    amount=Decimal("4.99"),
                    currency="USD",
                    active=True,
                    sort_order=100,
                ),
                CoinPackage(
                    code="custom_pack",
                    name="Custom",
                    coin_amount=777,
                    amount=Decimal("777.00"),
                    currency="RUB",
                    active=True,
                    sort_order=900,
                ),
            ]
        )
        await seed_default_coin_packages(session)
        active_packages = await list_active_coin_packages(session)

    active_codes = [package.code for package in active_packages]
    assert "coins_100" not in active_codes
    assert "custom_pack" in active_codes


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
        "coins_rub_450",
        "coins_rub_1200",
        "coins_rub_2600",
    ]
    assert [item["coin_amount"] for item in payload] == [450, 1200, 2600]
    assert all(item["active"] is True for item in payload)
