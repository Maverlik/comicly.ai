from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode, urlparse, urlunparse
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.models.payment import CoinPackage, Payment
from app.services.wallets import WalletTransactionReason, grant_coins
from app.services.yookassa import (
    YooKassaPaymentResult,
    YooKassaService,
    parse_webhook_payload,
)

PROVIDER_NAME = "yookassa"

PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_WAITING = "waiting_for_capture"
PAYMENT_STATUS_SUCCEEDED = "succeeded"
PAYMENT_STATUS_CANCELED = "canceled"

YOOKASSA_TO_INTERNAL_STATUS = {
    "pending": PAYMENT_STATUS_PENDING,
    "waiting_for_capture": PAYMENT_STATUS_WAITING,
    "succeeded": PAYMENT_STATUS_SUCCEEDED,
    "canceled": PAYMENT_STATUS_CANCELED,
}


@dataclass(frozen=True)
class CheckoutSession:
    payment_id: UUID
    confirmation_url: str
    status: str


@dataclass(frozen=True)
class PaymentStatusView:
    payment_id: UUID
    status: str
    coin_amount: int
    credited: bool


async def start_yookassa_checkout(
    session: AsyncSession,
    *,
    settings: Settings,
    yookassa: YooKassaService,
    user_id: UUID,
    coin_package_id: UUID,
) -> CheckoutSession:
    package = await _get_active_package(session, coin_package_id=coin_package_id)
    if package.currency.upper() != "RUB":
        raise ApiError(
            status_code=400,
            code="UNSUPPORTED_CURRENCY",
            message="Only RUB coin packages can be purchased via YooKassa.",
        )

    payment = Payment(
        user_id=user_id,
        coin_package_id=package.id,
        status=PAYMENT_STATUS_PENDING,
        amount=package.amount,
        currency=package.currency,
        provider=PROVIDER_NAME,
        idempotency_key=str(uuid4()),
    )
    session.add(payment)
    await session.flush()
    payment_internal_id = payment.id

    description = f"comicly.ai • {package.name} • {package.coin_amount} монет"
    return_url = _augment_return_url(
        settings.yookassa_return_url, payment_id=payment_internal_id
    )

    try:
        result = await yookassa.create_payment(
            amount=package.amount,
            currency=package.currency,
            description=description,
            idempotence_key=str(payment.idempotency_key),
            return_url=return_url,
            metadata={
                "payment_id": str(payment_internal_id),
                "user_id": str(user_id),
                "coin_package_id": str(package.id),
            },
        )
    except ApiError:
        await session.rollback()
        raise

    payment.provider_payment_id = result.payment_id
    payment.provider_checkout_id = result.payment_id
    payment.status = YOOKASSA_TO_INTERNAL_STATUS.get(
        result.status, PAYMENT_STATUS_PENDING
    )
    await session.flush()
    await session.commit()

    if not result.confirmation_url:
        raise ApiError(
            status_code=502,
            code="PAYMENT_CONFIRMATION_MISSING",
            message="Payment confirmation URL was not returned by provider.",
        )

    return CheckoutSession(
        payment_id=payment_internal_id,
        confirmation_url=result.confirmation_url,
        status=payment.status,
    )


async def apply_webhook_event(
    session: AsyncSession,
    *,
    yookassa: YooKassaService,
    payload: dict,
    event_id: str,
) -> None:
    event = parse_webhook_payload(payload)
    existing = await session.execute(
        select(Payment).where(Payment.webhook_event_id == event_id)
    )
    if existing.scalar_one_or_none() is not None:
        return

    fresh = await yookassa.get_payment(event.payment_id)
    payment = await _get_payment_by_provider_id(
        session, provider_payment_id=fresh.payment_id
    )
    await _apply_provider_status(
        session,
        payment=payment,
        fresh=fresh,
        webhook_event_id=event_id,
    )


async def refresh_payment_status(
    session: AsyncSession,
    *,
    yookassa: YooKassaService,
    user_id: UUID,
    payment_id: UUID,
) -> PaymentStatusView:
    payment = await _get_payment(session, payment_id=payment_id)
    if payment.user_id != user_id:
        raise ApiError(
            status_code=404,
            code="PAYMENT_NOT_FOUND",
            message="Payment record was not found.",
        )

    if payment.provider_payment_id and yookassa.is_configured:
        fresh = await yookassa.get_payment(payment.provider_payment_id)
        await _apply_provider_status(session, payment=payment, fresh=fresh)

    package = await _get_package(session, package_id=payment.coin_package_id)
    return PaymentStatusView(
        payment_id=payment.id,
        status=payment.status,
        coin_amount=package.coin_amount,
        credited=payment.status == PAYMENT_STATUS_SUCCEEDED,
    )


async def _apply_provider_status(
    session: AsyncSession,
    *,
    payment: Payment,
    fresh: YooKassaPaymentResult,
    webhook_event_id: str | None = None,
) -> None:
    if not _amounts_match(payment.amount, fresh.amount):
        raise ApiError(
            status_code=409,
            code="PAYMENT_AMOUNT_MISMATCH",
            message="Provider amount does not match expected payment.",
        )
    if payment.currency.upper() != fresh.currency.upper():
        raise ApiError(
            status_code=409,
            code="PAYMENT_CURRENCY_MISMATCH",
            message="Provider currency does not match expected payment.",
        )

    new_status = YOOKASSA_TO_INTERNAL_STATUS.get(fresh.status, payment.status)

    if payment.status == PAYMENT_STATUS_SUCCEEDED:
        if webhook_event_id and payment.webhook_event_id is None:
            payment.webhook_event_id = webhook_event_id
            await session.flush()
            await session.commit()
        return

    payment.status = new_status
    if webhook_event_id and payment.webhook_event_id is None:
        payment.webhook_event_id = webhook_event_id

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return

    if new_status == PAYMENT_STATUS_SUCCEEDED and fresh.paid:
        package = await _get_package(session, package_id=payment.coin_package_id)
        await grant_coins(
            session,
            user_id=payment.user_id,
            amount=package.coin_amount,
            reason=WalletTransactionReason.GRANT,
            reference_type="payment",
            reference_id=payment.id,
            idempotency_key=f"payment:{payment.id}:credit",
        )

    await session.commit()


async def _get_active_package(
    session: AsyncSession, *, coin_package_id: UUID
) -> CoinPackage:
    result = await session.execute(
        select(CoinPackage).where(CoinPackage.id == coin_package_id)
    )
    package = result.scalar_one_or_none()
    if package is None or not package.active:
        raise ApiError(
            status_code=404,
            code="COIN_PACKAGE_NOT_FOUND",
            message="Coin package was not found or is unavailable.",
        )
    return package


async def _get_package(session: AsyncSession, *, package_id: UUID) -> CoinPackage:
    result = await session.execute(
        select(CoinPackage).where(CoinPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    if package is None:
        raise ApiError(
            status_code=404,
            code="COIN_PACKAGE_NOT_FOUND",
            message="Coin package was not found.",
        )
    return package


async def _get_payment(session: AsyncSession, *, payment_id: UUID) -> Payment:
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise ApiError(
            status_code=404,
            code="PAYMENT_NOT_FOUND",
            message="Payment record was not found.",
        )
    return payment


async def _get_payment_by_provider_id(
    session: AsyncSession, *, provider_payment_id: str
) -> Payment:
    result = await session.execute(
        select(Payment).where(
            Payment.provider == PROVIDER_NAME,
            Payment.provider_payment_id == provider_payment_id,
        )
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise ApiError(
            status_code=404,
            code="PAYMENT_NOT_FOUND",
            message="Payment record was not found.",
        )
    return payment


def _amounts_match(left: Decimal, right: Decimal) -> bool:
    return Decimal(left).quantize(Decimal("0.01")) == Decimal(right).quantize(
        Decimal("0.01")
    )


def _augment_return_url(base_url: str, *, payment_id: UUID) -> str:
    parsed = urlparse(base_url)
    extra = urlencode({"payment_id": str(payment_id)})
    query = f"{parsed.query}&{extra}" if parsed.query else extra
    return urlunparse(parsed._replace(query=query))
