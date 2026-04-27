from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Select, desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.models.wallet import Wallet, WalletTransaction

RECENT_TRANSACTION_LIMIT = 10


class GenerationCostKind(StrEnum):
    FULL_PAGE = "full_page"
    SCENE_REGENERATION = "scene_regeneration"


class WalletTransactionReason(StrEnum):
    GRANT = "grant"
    ADJUSTMENT = "adjustment"
    GENERATION_DEBIT = "generation_debit"
    GENERATION_REFUND = "generation_refund"


@dataclass(frozen=True)
class WalletTransactionView:
    id: UUID
    amount: int
    balance_after: int
    reason: str
    reference_type: str | None
    reference_id: UUID | None
    idempotency_key: str | None
    created_at: datetime


@dataclass(frozen=True)
class WalletSummary:
    balance: int
    recent_transactions: list[WalletTransactionView]


@dataclass(frozen=True)
class WalletOperationResult:
    balance: int
    transaction: WalletTransactionView
    idempotent_replay: bool = False


def generation_cost(settings: Settings, kind: GenerationCostKind) -> int:
    if kind == GenerationCostKind.FULL_PAGE:
        return settings.full_page_generation_cost
    if kind == GenerationCostKind.SCENE_REGENERATION:
        return settings.scene_regeneration_cost
    raise ValueError(f"Unsupported generation cost kind: {kind}")


async def get_wallet_summary(
    session: AsyncSession,
    *,
    user_id: UUID,
    recent_limit: int = RECENT_TRANSACTION_LIMIT,
) -> WalletSummary:
    wallet = await _get_wallet(session, user_id=user_id)
    transactions = (
        await session.execute(
            _recent_transactions_query(user_id=user_id, limit=recent_limit)
        )
    ).scalars()
    return WalletSummary(
        balance=wallet.balance,
        recent_transactions=[
            _transaction_view(transaction) for transaction in transactions
        ],
    )


async def grant_coins(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount: int,
    reason: WalletTransactionReason = WalletTransactionReason.GRANT,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
    idempotency_key: str | None = None,
) -> WalletOperationResult:
    _require_positive_amount(amount)
    return await _record_positive_operation(
        session,
        user_id=user_id,
        amount=amount,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
    )


async def debit_generation_cost(
    session: AsyncSession,
    *,
    user_id: UUID,
    settings: Settings,
    kind: GenerationCostKind,
    reference_type: str | None,
    reference_id: UUID | None,
    idempotency_key: str | None,
) -> WalletOperationResult:
    cost = generation_cost(settings, kind)
    return await debit_coins(
        session,
        user_id=user_id,
        amount=cost,
        reason=WalletTransactionReason.GENERATION_DEBIT,
        reference_type=reference_type or kind.value,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
    )


async def debit_coins(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount: int,
    reason: WalletTransactionReason = WalletTransactionReason.GENERATION_DEBIT,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
    idempotency_key: str | None,
) -> WalletOperationResult:
    _require_positive_amount(amount)
    key = _require_idempotency_key(idempotency_key)
    existing = await _get_idempotent_transaction(session, key=key)
    if existing is not None:
        return _idempotent_result(existing, user_id=user_id)

    row = (
        (
            await session.execute(
                update(Wallet)
                .where(Wallet.user_id == user_id)
                .where(Wallet.balance >= amount)
                .values(balance=Wallet.balance - amount)
                .returning(Wallet.id, Wallet.balance)
            )
        )
        .mappings()
        .one_or_none()
    )

    if row is None:
        await _raise_wallet_missing_or_insufficient(session, user_id=user_id)

    transaction = WalletTransaction(
        wallet_id=row["id"],
        user_id=user_id,
        amount=-amount,
        balance_after=row["balance"],
        reason=reason.value,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=key,
        created_at=datetime.now(UTC),
    )
    return await _flush_transaction_with_idempotency_replay(
        session,
        transaction,
        user_id=user_id,
    )


async def refund_generation_debit(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount: int,
    reference_type: str | None,
    reference_id: UUID | None,
    idempotency_key: str | None,
) -> WalletOperationResult:
    key = _require_idempotency_key(idempotency_key)
    return await _record_positive_operation(
        session,
        user_id=user_id,
        amount=amount,
        reason=WalletTransactionReason.GENERATION_REFUND,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=key,
    )


async def _record_positive_operation(
    session: AsyncSession,
    *,
    user_id: UUID,
    amount: int,
    reason: WalletTransactionReason,
    reference_type: str | None,
    reference_id: UUID | None,
    idempotency_key: str | None,
) -> WalletOperationResult:
    _require_positive_amount(amount)
    key = idempotency_key.strip() if idempotency_key else None
    existing = None
    if key:
        existing = await _get_idempotent_transaction(session, key=key)
    if existing is not None:
        return _idempotent_result(existing, user_id=user_id)

    wallet = await _get_or_create_wallet(session, user_id=user_id)
    row = (
        (
            await session.execute(
                update(Wallet)
                .where(Wallet.id == wallet.id)
                .values(balance=Wallet.balance + amount)
                .returning(Wallet.id, Wallet.balance)
            )
        )
        .mappings()
        .one()
    )
    transaction = WalletTransaction(
        wallet_id=row["id"],
        user_id=user_id,
        amount=amount,
        balance_after=row["balance"],
        reason=reason.value,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=key,
        created_at=datetime.now(UTC),
    )
    return await _flush_transaction_with_idempotency_replay(
        session,
        transaction,
        user_id=user_id,
    )


async def _flush_transaction_with_idempotency_replay(
    session: AsyncSession,
    transaction: WalletTransaction,
    *,
    user_id: UUID,
) -> WalletOperationResult:
    session.add(transaction)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        if transaction.idempotency_key is None:
            raise
        existing = await _get_idempotent_transaction(
            session,
            key=transaction.idempotency_key,
        )
        if existing is None:
            raise exc
        return _idempotent_result(existing, user_id=user_id)

    return WalletOperationResult(
        balance=transaction.balance_after,
        transaction=_transaction_view(transaction),
    )


async def _get_or_create_wallet(session: AsyncSession, *, user_id: UUID) -> Wallet:
    wallet = await _get_wallet_or_none(session, user_id=user_id)
    if wallet is not None:
        return wallet

    wallet = Wallet(user_id=user_id, balance=0)
    session.add(wallet)
    await session.flush()
    return wallet


async def _get_wallet(session: AsyncSession, *, user_id: UUID) -> Wallet:
    wallet = await _get_wallet_or_none(session, user_id=user_id)
    if wallet is None:
        raise ApiError(
            status_code=404,
            code="WALLET_NOT_FOUND",
            message="Wallet was not found.",
        )
    return wallet


async def _get_wallet_or_none(session: AsyncSession, *, user_id: UUID) -> Wallet | None:
    result = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_idempotent_transaction(
    session: AsyncSession,
    *,
    key: str,
) -> WalletTransaction | None:
    result = await session.execute(
        select(WalletTransaction).where(WalletTransaction.idempotency_key == key)
    )
    return result.scalar_one_or_none()


def _idempotent_result(
    transaction: WalletTransaction,
    *,
    user_id: UUID,
) -> WalletOperationResult:
    if transaction.user_id != user_id:
        raise ApiError(
            status_code=409,
            code="IDEMPOTENCY_KEY_CONFLICT",
            message="Idempotency key belongs to another wallet operation.",
        )
    return WalletOperationResult(
        balance=transaction.balance_after,
        transaction=_transaction_view(transaction),
        idempotent_replay=True,
    )


async def _raise_wallet_missing_or_insufficient(
    session: AsyncSession,
    *,
    user_id: UUID,
) -> None:
    wallet = await _get_wallet_or_none(session, user_id=user_id)
    if wallet is None:
        raise ApiError(
            status_code=404,
            code="WALLET_NOT_FOUND",
            message="Wallet was not found.",
        )
    raise ApiError(
        status_code=409,
        code="INSUFFICIENT_COINS",
        message="Not enough coins for this operation.",
    )


def _recent_transactions_query(
    *,
    user_id: UUID,
    limit: int,
) -> Select[tuple[WalletTransaction]]:
    return (
        select(WalletTransaction)
        .where(WalletTransaction.user_id == user_id)
        .order_by(desc(WalletTransaction.created_at), desc(WalletTransaction.id))
        .limit(limit)
    )


def _transaction_view(transaction: WalletTransaction) -> WalletTransactionView:
    return WalletTransactionView(
        id=transaction.id,
        amount=transaction.amount,
        balance_after=transaction.balance_after,
        reason=transaction.reason,
        reference_type=transaction.reference_type,
        reference_id=transaction.reference_id,
        idempotency_key=transaction.idempotency_key,
        created_at=transaction.created_at,
    )


def _require_positive_amount(amount: int) -> None:
    if amount <= 0:
        raise ApiError(
            status_code=400,
            code="INVALID_WALLET_AMOUNT",
            message="Wallet amount must be greater than zero.",
        )


def _require_idempotency_key(idempotency_key: str | None) -> str:
    key = (idempotency_key or "").strip()
    if not key:
        raise ApiError(
            status_code=400,
            code="IDEMPOTENCY_KEY_REQUIRED",
            message="Idempotency-Key header is required for billable operations.",
        )
    return key
