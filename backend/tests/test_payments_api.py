from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.v1.payments import get_yookassa_service
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.payment import CoinPackage, Payment
from app.models.user import User, UserSession
from app.models.wallet import Wallet, WalletTransaction
from app.services.auth_sessions import hash_session_token
from app.services.yookassa import YooKassaService


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


def _build_settings(**overrides) -> Settings:
    base = {
        "yookassa_shop_id": "shop_test",
        "yookassa_api_key": "secret_test",
        "yookassa_return_url": "https://comicly.ai/pricing.html?payment=return",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def _yookassa_with_mock(
    settings: Settings,
    handler,
) -> YooKassaService:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return YooKassaService(settings, http_client=client)


@pytest.fixture
async def app_client_factory(
    session_maker: async_sessionmaker[AsyncSession],
):
    clients: list[AsyncClient] = []

    async def factory(
        *,
        settings: Settings | None = None,
        yookassa: YooKassaService | None = None,
    ) -> AsyncClient:
        app_settings = settings or _build_settings()
        app = create_app(app_settings)

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with session_maker() as session:
                yield session

        app.dependency_overrides[get_async_session] = override_session
        app.dependency_overrides[get_settings] = lambda: app_settings
        if yookassa is not None:
            app.dependency_overrides[get_yookassa_service] = lambda: yookassa

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://testserver")
        await client.__aenter__()
        clients.append(client)
        return client

    yield factory

    for client in clients:
        await client.__aexit__(None, None, None)


async def _seed_user_and_package(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    token: str = "valid-token",
    balance: int = 0,
    package_amount: Decimal = Decimal("199.00"),
    package_coins: int = 450,
    package_currency: str = "RUB",
) -> tuple[User, CoinPackage]:
    async with session_maker() as session:
        user = User(email="buyer@example.com", display_name="Buyer")
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
        package = CoinPackage(
            code="coins_rub_450",
            name="Старт",
            coin_amount=package_coins,
            amount=package_amount,
            currency=package_currency,
            active=True,
            sort_order=10,
        )
        session.add(package)
        await session.commit()
        await session.refresh(user)
        await session.refresh(package)
        return user, package


async def test_create_payment_requires_authentication(app_client_factory) -> None:
    client = await app_client_factory()
    response = await client.post(
        "/api/v1/payments",
        json={"coin_package_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_create_payment_unavailable_when_provider_not_configured(
    app_client_factory,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, package = await _seed_user_and_package(session_maker)
    settings = _build_settings(yookassa_shop_id=None, yookassa_api_key=None)
    yookassa = YooKassaService(settings)
    client = await app_client_factory(settings=settings, yookassa=yookassa)

    response = await client.post(
        "/api/v1/payments",
        json={"coin_package_id": str(package.id)},
        cookies={"comicly_session": "valid-token"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PAYMENTS_UNAVAILABLE"


async def test_create_payment_returns_confirmation_url(
    app_client_factory,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    _, package = await _seed_user_and_package(session_maker)

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["idempotence"] = request.headers.get("Idempotence-Key")
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={
                "id": "yk_pay_123",
                "status": "pending",
                "paid": False,
                "amount": {"value": "199.00", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "confirmation_url": "https://yoomoney.test/checkout/yk_pay_123",
                },
            },
        )

    settings = _build_settings()
    yookassa = _yookassa_with_mock(settings, handler)
    client = await app_client_factory(settings=settings, yookassa=yookassa)

    response = await client.post(
        "/api/v1/payments",
        json={"coin_package_id": str(package.id)},
        cookies={"comicly_session": "valid-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confirmation_url"] == "https://yoomoney.test/checkout/yk_pay_123"
    assert body["status"] == "pending"
    assert captured["url"].endswith("/v3/payments")
    assert captured["idempotence"]
    assert captured["auth"].startswith("Basic ")

    async with session_maker() as session:
        rows = (await session.execute(select(Payment))).scalars().all()
        assert len(rows) == 1
        assert rows[0].provider == "yookassa"
        assert rows[0].provider_payment_id == "yk_pay_123"
        assert rows[0].status == "pending"


async def test_webhook_credits_coins_on_succeeded_event(
    app_client_factory,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, package = await _seed_user_and_package(session_maker)

    async with session_maker() as session:
        payment = Payment(
            user_id=user.id,
            coin_package_id=package.id,
            status="pending",
            amount=package.amount,
            currency=package.currency,
            provider="yookassa",
            provider_payment_id="yk_pay_999",
            idempotency_key="local-key-1",
        )
        session.add(payment)
        await session.commit()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path.endswith("/payments/yk_pay_999")
        return httpx.Response(
            200,
            json={
                "id": "yk_pay_999",
                "status": "succeeded",
                "paid": True,
                "amount": {"value": "199.00", "currency": "RUB"},
            },
        )

    settings = _build_settings()
    yookassa = _yookassa_with_mock(settings, handler)
    client = await app_client_factory(settings=settings, yookassa=yookassa)

    response = await client.post(
        "/api/v1/payments/webhook",
        json={
            "type": "notification",
            "event": "payment.succeeded",
            "object": {"id": "yk_pay_999", "status": "succeeded"},
        },
        headers={"Idempotency-Key": "evt-1"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True

    async with session_maker() as session:
        result = await session.execute(
            select(Payment).where(Payment.provider_payment_id == "yk_pay_999")
        )
        payment = result.scalar_one()
        assert payment.status == "succeeded"
        assert payment.webhook_event_id == "evt-1"

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        assert wallet.balance == package.coin_amount

        txn_count = len(
            (
                await session.execute(
                    select(WalletTransaction).where(
                        WalletTransaction.user_id == user.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert txn_count == 1


async def test_webhook_is_idempotent_for_replays(
    app_client_factory,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, package = await _seed_user_and_package(session_maker)

    async with session_maker() as session:
        session.add(
            Payment(
                user_id=user.id,
                coin_package_id=package.id,
                status="pending",
                amount=package.amount,
                currency=package.currency,
                provider="yookassa",
                provider_payment_id="yk_pay_42",
                idempotency_key="local-key-42",
            )
        )
        await session.commit()

    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        return httpx.Response(
            200,
            json={
                "id": "yk_pay_42",
                "status": "succeeded",
                "paid": True,
                "amount": {"value": "199.00", "currency": "RUB"},
            },
        )

    settings = _build_settings()
    yookassa = _yookassa_with_mock(settings, handler)
    client = await app_client_factory(settings=settings, yookassa=yookassa)

    body = {
        "type": "notification",
        "event": "payment.succeeded",
        "object": {"id": "yk_pay_42", "status": "succeeded"},
    }
    first = await client.post(
        "/api/v1/payments/webhook",
        json=body,
        headers={"Idempotency-Key": "dup-evt"},
    )
    second = await client.post(
        "/api/v1/payments/webhook",
        json=body,
        headers={"Idempotency-Key": "dup-evt"},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    async with session_maker() as session:
        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        assert wallet.balance == package.coin_amount

        txn_count = len(
            (
                await session.execute(
                    select(WalletTransaction).where(
                        WalletTransaction.user_id == user.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert txn_count == 1

    assert call_count["value"] == 1


async def test_webhook_rejects_amount_mismatch(
    app_client_factory,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, package = await _seed_user_and_package(session_maker)

    async with session_maker() as session:
        session.add(
            Payment(
                user_id=user.id,
                coin_package_id=package.id,
                status="pending",
                amount=package.amount,
                currency=package.currency,
                provider="yookassa",
                provider_payment_id="yk_pay_amt",
                idempotency_key="local-key-amt",
            )
        )
        await session.commit()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "yk_pay_amt",
                "status": "succeeded",
                "paid": True,
                "amount": {"value": "0.01", "currency": "RUB"},
            },
        )

    settings = _build_settings()
    yookassa = _yookassa_with_mock(settings, handler)
    client = await app_client_factory(settings=settings, yookassa=yookassa)

    response = await client.post(
        "/api/v1/payments/webhook",
        json={
            "type": "notification",
            "event": "payment.succeeded",
            "object": {"id": "yk_pay_amt", "status": "succeeded"},
        },
        headers={"Idempotency-Key": "evt-amt"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAYMENT_AMOUNT_MISMATCH"

    async with session_maker() as session:
        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == user.id))
        ).scalar_one()
        assert wallet.balance == 0
