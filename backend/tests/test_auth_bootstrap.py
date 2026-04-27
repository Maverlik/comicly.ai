from collections.abc import AsyncIterator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base
from app.models.user import ProviderIdentity, User
from app.models.wallet import Wallet, WalletTransaction
from app.services.auth_bootstrap import AuthBootstrapService
from app.services.oauth_providers import OAuthProfile


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


async def test_first_oauth_login_bootstraps_user_profile_wallet_and_starter_grant(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    settings = Settings(_env_file=None, starter_coins=150)
    service = AuthBootstrapService(settings)

    async with session_maker() as session:
        user = await service.bootstrap_oauth_user(
            session,
            profile=OAuthProfile(
                provider="google",
                provider_user_id="google-1",
                email="user@example.com",
                email_verified=True,
                display_name="User One",
                avatar_url="https://example.com/avatar.png",
            ),
        )
        await session.commit()

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transaction = (
            await session.execute(
                select(WalletTransaction).where(WalletTransaction.user_id == user.id)
            )
        ).scalar_one()

    assert user.email == "user@example.com"
    assert user.display_name == "User One"
    assert user.avatar_url == "https://example.com/avatar.png"
    assert wallet.balance == 150
    assert transaction.amount == 150
    assert transaction.balance_after == 150
    assert transaction.idempotency_key == f"starter-grant:{user.id}"


async def test_returning_provider_login_reuses_existing_user(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    service = AuthBootstrapService(Settings(_env_file=None))
    profile = OAuthProfile(
        provider="google",
        provider_user_id="same-google-id",
        email="user@example.com",
        email_verified=True,
        display_name="User One",
        avatar_url=None,
    )

    async with session_maker() as session:
        first = await service.bootstrap_oauth_user(session, profile=profile)
        second = await service.bootstrap_oauth_user(session, profile=profile)
        await session.commit()

        identities = (await session.execute(select(ProviderIdentity))).scalars().all()
        transactions = (
            (await session.execute(select(WalletTransaction))).scalars().all()
        )

    assert second.id == first.id
    assert len(identities) == 1
    assert len(transactions) == 1


async def test_second_provider_with_verified_email_links_existing_user(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    service = AuthBootstrapService(Settings(_env_file=None))

    async with session_maker() as session:
        google_user = await service.bootstrap_oauth_user(
            session,
            profile=OAuthProfile(
                provider="google",
                provider_user_id="google-1",
                email="same@example.com",
                email_verified=True,
                display_name="Google User",
                avatar_url=None,
            ),
        )
        yandex_user = await service.bootstrap_oauth_user(
            session,
            profile=OAuthProfile(
                provider="yandex",
                provider_user_id="yandex-1",
                email="same@example.com",
                email_verified=True,
                display_name="Yandex User",
                avatar_url=None,
            ),
        )
        await session.commit()

        users = (await session.execute(select(User))).scalars().all()
        identities = (await session.execute(select(ProviderIdentity))).scalars().all()
        transactions = (
            (await session.execute(select(WalletTransaction))).scalars().all()
        )

    assert yandex_user.id == google_user.id
    assert len(users) == 1
    assert len(identities) == 2
    assert len(transactions) == 1


async def test_unverified_email_does_not_link_accounts(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    service = AuthBootstrapService(Settings(_env_file=None))

    async with session_maker() as session:
        first = await service.bootstrap_oauth_user(
            session,
            profile=OAuthProfile(
                provider="google",
                provider_user_id="google-1",
                email="same@example.com",
                email_verified=True,
                display_name=None,
                avatar_url=None,
            ),
        )
        second = await service.bootstrap_oauth_user(
            session,
            profile=OAuthProfile(
                provider="yandex",
                provider_user_id="yandex-1",
                email="same@example.com",
                email_verified=False,
                display_name=None,
                avatar_url=None,
            ),
        )
        await session.commit()

        users = (await session.execute(select(User))).scalars().all()

    assert second.id != first.id
    assert len(users) == 2
