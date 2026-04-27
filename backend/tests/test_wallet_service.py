import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import Settings
from app.core.errors import ApiError
from app.db.base import Base
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.services.wallets import (
    GenerationCostKind,
    WalletTransactionReason,
    debit_generation_cost,
    get_wallet_summary,
    grant_coins,
    refund_generation_debit,
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


async def create_user_wallet(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    balance: int = 100,
) -> User:
    async with session_maker() as session:
        user = User(email=f"{uuid4()}@example.com", display_name="User")
        session.add(user)
        await session.flush()
        session.add(Wallet(user_id=user.id, balance=balance))
        await session.commit()
        return user


async def transaction_count(session: AsyncSession) -> int:
    count = await session.scalar(select(func.count()).select_from(WalletTransaction))
    return count or 0


async def test_grant_records_transaction_and_updates_wallet(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=10)

    async with session_maker() as session:
        result = await grant_coins(
            session,
            user_id=user.id,
            amount=15,
            reason=WalletTransactionReason.ADJUSTMENT,
            reference_type="test",
            reference_id=user.id,
            idempotency_key="grant-1",
        )
        await session.commit()

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transaction = (await session.execute(select(WalletTransaction))).scalar_one()

    assert result.balance == 25
    assert wallet.balance == 25
    assert transaction.amount == 15
    assert transaction.balance_after == 25
    assert transaction.reason == "adjustment"
    assert transaction.idempotency_key == "grant-1"


async def test_generation_debit_uses_configured_cost_and_records_transaction(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=50)
    settings = Settings(
        _env_file=None,
        full_page_generation_cost=20,
        scene_regeneration_cost=4,
    )

    async with session_maker() as session:
        result = await debit_generation_cost(
            session,
            user_id=user.id,
            settings=settings,
            kind=GenerationCostKind.FULL_PAGE,
            reference_type="generation_job",
            reference_id=user.id,
            idempotency_key="debit-full-page",
        )
        await session.commit()

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transaction = (await session.execute(select(WalletTransaction))).scalar_one()

    assert result.balance == 30
    assert wallet.balance == 30
    assert transaction.amount == -20
    assert transaction.balance_after == 30
    assert transaction.reason == "generation_debit"
    assert transaction.reference_type == "generation_job"


async def test_scene_regeneration_debit_uses_configured_cost(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=10)
    settings = Settings(_env_file=None, scene_regeneration_cost=4)

    async with session_maker() as session:
        result = await debit_generation_cost(
            session,
            user_id=user.id,
            settings=settings,
            kind=GenerationCostKind.SCENE_REGENERATION,
            reference_type="generation_job",
            reference_id=user.id,
            idempotency_key="debit-scene",
        )
        await session.commit()

    assert result.balance == 6
    assert result.transaction.amount == -4


async def test_billable_debit_requires_idempotency_key(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=50)

    async with session_maker() as session:
        with pytest.raises(ApiError) as exc_info:
            await debit_generation_cost(
                session,
                user_id=user.id,
                settings=Settings(_env_file=None),
                kind=GenerationCostKind.FULL_PAGE,
                reference_type="generation_job",
                reference_id=user.id,
                idempotency_key=None,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "IDEMPOTENCY_KEY_REQUIRED"
        assert await transaction_count(session) == 0


async def test_duplicate_idempotency_key_does_not_double_debit(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=50)
    settings = Settings(_env_file=None, full_page_generation_cost=20)

    async with session_maker() as session:
        first = await debit_generation_cost(
            session,
            user_id=user.id,
            settings=settings,
            kind=GenerationCostKind.FULL_PAGE,
            reference_type="generation_job",
            reference_id=user.id,
            idempotency_key="same-debit",
        )
        second = await debit_generation_cost(
            session,
            user_id=user.id,
            settings=settings,
            kind=GenerationCostKind.FULL_PAGE,
            reference_type="generation_job",
            reference_id=user.id,
            idempotency_key="same-debit",
        )
        await session.commit()

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transactions = (
            (await session.execute(select(WalletTransaction))).scalars().all()
        )

    assert first.balance == 30
    assert second.balance == 30
    assert second.idempotent_replay is True
    assert wallet.balance == 30
    assert len(transactions) == 1


async def test_insufficient_funds_do_not_create_debit_transaction(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=5)

    async with session_maker() as session:
        with pytest.raises(ApiError) as exc_info:
            await debit_generation_cost(
                session,
                user_id=user.id,
                settings=Settings(_env_file=None, full_page_generation_cost=20),
                kind=GenerationCostKind.FULL_PAGE,
                reference_type="generation_job",
                reference_id=user.id,
                idempotency_key="too-expensive",
            )

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transactions = await transaction_count(session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "INSUFFICIENT_COINS"
    assert wallet.balance == 5
    assert transactions == 0


async def test_refund_restores_balance_once(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=50)
    settings = Settings(_env_file=None, full_page_generation_cost=20)

    async with session_maker() as session:
        debit = await debit_generation_cost(
            session,
            user_id=user.id,
            settings=settings,
            kind=GenerationCostKind.FULL_PAGE,
            reference_type="generation_job",
            reference_id=user.id,
            idempotency_key="debit-before-failure",
        )
        first_refund = await refund_generation_debit(
            session,
            user_id=user.id,
            amount=20,
            reference_type="wallet_transaction",
            reference_id=debit.transaction.id,
            idempotency_key="refund-after-failure",
        )
        second_refund = await refund_generation_debit(
            session,
            user_id=user.id,
            amount=20,
            reference_type="wallet_transaction",
            reference_id=debit.transaction.id,
            idempotency_key="refund-after-failure",
        )
        await session.commit()

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transactions = (
            (
                await session.execute(
                    select(WalletTransaction).order_by(WalletTransaction.amount)
                )
            )
            .scalars()
            .all()
        )

    assert first_refund.balance == 50
    assert second_refund.balance == 50
    assert second_refund.idempotent_replay is True
    assert wallet.balance == 50
    assert [transaction.amount for transaction in transactions] == [-20, 20]


async def test_wallet_summary_balance_matches_recent_history(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=0)

    async with session_maker() as session:
        for index in range(12):
            await grant_coins(
                session,
                user_id=user.id,
                amount=1,
                reference_type="test",
                reference_id=user.id,
                idempotency_key=f"grant-{index}",
            )
        await session.commit()

        summary = await get_wallet_summary(session, user_id=user.id)

    assert summary.balance == 12
    assert len(summary.recent_transactions) == 10
    assert all(
        transaction.balance_after <= 12 for transaction in summary.recent_transactions
    )


async def test_concurrent_debits_cannot_create_negative_balance(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user_wallet(session_maker, balance=30)
    settings = Settings(_env_file=None, full_page_generation_cost=20)

    async def attempt_debit(key: str) -> str:
        async with session_maker() as session:
            try:
                await debit_generation_cost(
                    session,
                    user_id=user.id,
                    settings=settings,
                    kind=GenerationCostKind.FULL_PAGE,
                    reference_type="generation_job",
                    reference_id=user.id,
                    idempotency_key=key,
                )
                await session.commit()
            except ApiError as exc:
                await session.rollback()
                return exc.code
            return "ok"

    results = await asyncio_gather_debits(attempt_debit)

    async with session_maker() as session:
        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        transactions = (
            (await session.execute(select(WalletTransaction))).scalars().all()
        )

    assert sorted(results) == ["INSUFFICIENT_COINS", "ok"]
    assert wallet.balance == 10
    assert len(transactions) == 1


async def asyncio_gather_debits(attempt_debit):
    return await asyncio.gather(
        attempt_debit("concurrent-a"),
        attempt_debit("concurrent-b"),
    )
