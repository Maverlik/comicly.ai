from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import CoinPackage


class CoinPackageSeed(NamedTuple):
    code: str
    name: str
    coin_amount: int
    amount: Decimal
    currency: str
    sort_order: int


DEFAULT_COIN_PACKAGES = (
    CoinPackageSeed("coins_100", "100 coins", 100, Decimal("4.99"), "USD", 100),
    CoinPackageSeed("coins_500", "500 coins", 500, Decimal("19.99"), "USD", 500),
    CoinPackageSeed("coins_1000", "1000 coins", 1000, Decimal("34.99"), "USD", 1000),
)


async def seed_default_coin_packages(session: AsyncSession) -> list[CoinPackage]:
    for package in DEFAULT_COIN_PACKAGES:
        result = await session.execute(
            select(CoinPackage).where(CoinPackage.code == package.code)
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(
                CoinPackage(
                    code=package.code,
                    name=package.name,
                    coin_amount=package.coin_amount,
                    amount=package.amount,
                    currency=package.currency,
                    active=True,
                    sort_order=package.sort_order,
                )
            )
            continue

        existing.name = package.name
        existing.coin_amount = package.coin_amount
        existing.amount = package.amount
        existing.currency = package.currency
        existing.active = True
        existing.sort_order = package.sort_order

    await session.flush()
    return await list_active_coin_packages(session)


async def list_active_coin_packages(session: AsyncSession) -> list[CoinPackage]:
    result = await session.execute(
        select(CoinPackage)
        .where(CoinPackage.active.is_(True))
        .order_by(CoinPackage.sort_order, CoinPackage.coin_amount)
    )
    return list(result.scalars().all())
