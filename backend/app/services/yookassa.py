from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ApiError

YOOKASSA_PAYMENTS_PATH = "/payments"
SUPPORTED_EVENTS = {
    "payment.succeeded",
    "payment.canceled",
    "payment.waiting_for_capture",
}


@dataclass(frozen=True)
class YooKassaPaymentResult:
    payment_id: str
    status: str
    confirmation_url: str | None
    amount: Decimal
    currency: str
    paid: bool
    raw: dict[str, Any]


@dataclass(frozen=True)
class YooKassaWebhookEvent:
    event: str
    payment_id: str
    raw: dict[str, Any]


class YooKassaError(ApiError):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(
            status_code=status_code,
            code="YOOKASSA_PROVIDER_ERROR",
            message=message,
        )


class YooKassaService:
    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._http_client = http_client

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.yookassa_shop_id and self._settings.yookassa_api_key)

    async def create_payment(
        self,
        *,
        amount: Decimal,
        currency: str,
        description: str,
        idempotence_key: str,
        return_url: str,
        metadata: dict[str, str] | None = None,
    ) -> YooKassaPaymentResult:
        self._require_configured()
        body: dict[str, Any] = {
            "amount": {
                "value": _format_amount(amount),
                "currency": currency,
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
            "description": description[:128],
        }
        if metadata:
            body["metadata"] = metadata

        data = await self._request(
            method="POST",
            path=YOOKASSA_PAYMENTS_PATH,
            json=body,
            headers={"Idempotence-Key": idempotence_key},
        )
        return _parse_payment(data)

    async def get_payment(self, payment_id: str) -> YooKassaPaymentResult:
        self._require_configured()
        data = await self._request(
            method="GET",
            path=f"{YOOKASSA_PAYMENTS_PATH}/{payment_id}",
        )
        return _parse_payment(data)

    async def _request(
        self,
        *,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._settings.yookassa_api_url.rstrip('/')}{path}"
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)

        auth = (
            self._settings.yookassa_shop_id or "",
            self._settings.yookassa_api_key or "",
        )

        async with self._client_context() as client:
            try:
                response = await client.request(
                    method,
                    url,
                    json=json,
                    headers=request_headers,
                    auth=auth,
                    timeout=self._settings.yookassa_request_timeout_seconds,
                )
            except httpx.HTTPError as exc:
                raise YooKassaError("YooKassa request failed.") from exc

        if response.status_code >= 500:
            raise YooKassaError("YooKassa is unavailable.", status_code=502)

        try:
            payload = response.json()
        except ValueError as exc:
            raise YooKassaError("YooKassa returned invalid JSON.") from exc

        if response.status_code >= 400:
            raise YooKassaError(
                _provider_error_message(payload),
                status_code=502,
            )

        if not isinstance(payload, dict):
            raise YooKassaError("YooKassa returned unexpected payload.")
        return payload

    def _client_context(self):
        if self._http_client is not None:
            return _NoopAsyncClient(self._http_client)
        return httpx.AsyncClient()

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise ApiError(
                status_code=503,
                code="PAYMENTS_UNAVAILABLE",
                message="Payments are not configured.",
            )


class _NoopAsyncClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


def _format_amount(amount: Decimal) -> str:
    quantized = Decimal(amount).quantize(Decimal("0.01"))
    return f"{quantized:.2f}"


def _parse_payment(data: dict[str, Any]) -> YooKassaPaymentResult:
    payment_id = data.get("id")
    status = data.get("status")
    if not payment_id or not status:
        raise YooKassaError("YooKassa response missing required fields.")

    amount_block = data.get("amount") or {}
    try:
        amount = Decimal(str(amount_block.get("value", "0")))
    except (TypeError, ValueError) as exc:
        raise YooKassaError("YooKassa amount is invalid.") from exc

    currency = str(amount_block.get("currency") or "")
    confirmation = data.get("confirmation") or {}
    confirmation_url = confirmation.get("confirmation_url")
    paid = bool(data.get("paid"))

    return YooKassaPaymentResult(
        payment_id=str(payment_id),
        status=str(status),
        confirmation_url=str(confirmation_url) if confirmation_url else None,
        amount=amount,
        currency=currency,
        paid=paid,
        raw=data,
    )


def _provider_error_message(payload: dict[str, Any]) -> str:
    description = payload.get("description") or payload.get("error_description")
    return (
        f"YooKassa rejected request: {description}"
        if description
        else ("YooKassa rejected request.")
    )


def parse_webhook_payload(payload: dict[str, Any]) -> YooKassaWebhookEvent:
    event = payload.get("event")
    obj = payload.get("object") or {}
    payment_id = obj.get("id") if isinstance(obj, dict) else None
    if not isinstance(event, str) or event not in SUPPORTED_EVENTS:
        raise ApiError(
            status_code=400,
            code="WEBHOOK_EVENT_UNSUPPORTED",
            message="Webhook event is not supported.",
        )
    if not payment_id or not isinstance(payment_id, str):
        raise ApiError(
            status_code=400,
            code="WEBHOOK_PAYLOAD_INVALID",
            message="Webhook payload is invalid.",
        )
    return YooKassaWebhookEvent(event=event, payment_id=payment_id, raw=payload)


def is_ip_allowed(client_ip: str | None, allowlist: list[str]) -> bool:
    if not client_ip:
        return False
    try:
        ip_obj = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for entry in allowlist:
        try:
            if "/" in entry:
                if ip_obj in ipaddress.ip_network(entry, strict=False):
                    return True
            elif ip_obj == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False
