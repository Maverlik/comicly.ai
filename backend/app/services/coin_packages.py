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
    CoinPackageSeed("coins_rub_450", "Старт", 450, Decimal("199.00"), "RUB", 100),
    CoinPackageSeed(
        "coins_rub_1200", "Оптимальный", 1200, Decimal("499.00"), "RUB", 200
    ),
    CoinPackageSeed(
        "coins_rub_2600", "Продвинутый", 2600, Decimal("999.00"), "RUB", 300
    ),
)
DEFAULT_COIN_PACKAGE_CODES = {package.code for package in DEFAULT_COIN_PACKAGES}
LEGACY_DEFAULT_COIN_PACKAGE_CODES = {"coins_100", "coins_500", "coins_1000"}


async def ensure_default_coin_packages(session: AsyncSession) -> list[CoinPackage]:
    result = await session.execute(
        select(CoinPackage)
        .where(
            CoinPackage.code.in_(
                DEFAULT_COIN_PACKAGE_CODES | LEGACY_DEFAULT_COIN_PACKAGE_CODES
            )
        )
        .where(CoinPackage.active.is_(True))
    )
    active_codes = {package.code for package in result.scalars()}
    if active_codes == DEFAULT_COIN_PACKAGE_CODES:
        return await list_active_coin_packages(session)
    return await seed_default_coin_packages(session)


async def seed_default_coin_packages(session: AsyncSession) -> list[CoinPackage]:
    legacy_result = await session.execute(
        select(CoinPackage).where(
            CoinPackage.code.in_(LEGACY_DEFAULT_COIN_PACKAGE_CODES)
        )
    )
    for legacy_package in legacy_result.scalars():
        legacy_package.active = False

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
