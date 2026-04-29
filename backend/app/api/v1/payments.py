from __future__ import annotations

import json
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.session import get_async_session
from app.services.current_user import CurrentUserContext, get_current_user
from app.services.payments import apply_webhook_event, start_yookassa_checkout
from app.services.yookassa import YooKassaService, is_ip_allowed

router = APIRouter(prefix="/payments", tags=["payments"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]
MAX_WEBHOOK_BYTES = 32 * 1024


def get_yookassa_service(settings: SettingsDep) -> YooKassaService:
    return YooKassaService(settings)


YooKassaDep = Annotated[YooKassaService, Depends(get_yookassa_service)]


class CreatePaymentRequest(BaseModel):
    coin_package_id: UUID


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    confirmation_url: str
    status: str


class WebhookAck(BaseModel):
    ok: bool


@router.post("", response_model=CreatePaymentResponse)
async def create_payment(
    payload: CreatePaymentRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
    yookassa: YooKassaDep,
) -> CreatePaymentResponse:
    if not yookassa.is_configured:
        raise ApiError(
            status_code=503,
            code="PAYMENTS_UNAVAILABLE",
            message="Payments are not configured.",
        )

    checkout = await start_yookassa_checkout(
        session,
        settings=settings,
        yookassa=yookassa,
        user_id=current_user.user.id,
        coin_package_id=payload.coin_package_id,
    )
    return CreatePaymentResponse(
        payment_id=checkout.payment_id,
        confirmation_url=checkout.confirmation_url,
        status=checkout.status,
    )


@router.post("/webhook", response_model=WebhookAck)
async def yookassa_webhook(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    yookassa: YooKassaDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> WebhookAck:
    _enforce_ip_allowlist(request, settings)
    raw = await request.body()
    if len(raw) > MAX_WEBHOOK_BYTES:
        raise ApiError(
            status_code=413,
            code="WEBHOOK_BODY_TOO_LARGE",
            message="Webhook body exceeds allowed size.",
        )

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(
            status_code=400,
            code="WEBHOOK_PAYLOAD_INVALID",
            message="Webhook payload is invalid.",
        ) from exc

    if not isinstance(payload, dict):
        raise ApiError(
            status_code=400,
            code="WEBHOOK_PAYLOAD_INVALID",
            message="Webhook payload is invalid.",
        )

    event_id = (idempotency_key or "").strip() or _derive_event_id(payload)
    await apply_webhook_event(
        session,
        yookassa=yookassa,
        payload=payload,
        event_id=event_id,
    )
    return WebhookAck(ok=True)


def _enforce_ip_allowlist(request: Request, settings: Settings) -> None:
    if not settings.yookassa_webhook_ip_check_enabled:
        return
    if not settings.is_production:
        return

    forwarded = request.headers.get("x-forwarded-for")
    candidate = (
        forwarded.split(",", 1)[0].strip()
        if forwarded
        else (request.client.host if request.client else None)
    )
    allowlist = settings.yookassa_webhook_ip_allowlist_entries
    if not allowlist or not is_ip_allowed(candidate, allowlist):
        raise ApiError(
            status_code=403,
            code="WEBHOOK_IP_FORBIDDEN",
            message="Webhook source is not allowed.",
        )


def _derive_event_id(payload: dict) -> str:
    obj = payload.get("object")
    event = payload.get("event")
    if isinstance(obj, dict):
        payment_id = obj.get("id")
        if isinstance(payment_id, str) and isinstance(event, str):
            return f"{event}:{payment_id}"
    return f"yookassa:{uuid4()}"
