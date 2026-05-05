from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.feedback import get_feedback_mailer
from app.main import create_app
from app.services.feedback import (
    FeedbackAttachment,
    FeedbackDeliveryError,
    FeedbackMessage,
)


class FakeFeedbackMailer:
    def __init__(self, *, configured: bool = True, should_fail: bool = False) -> None:
        self.is_configured = configured
        self.should_fail = should_fail
        self.messages: list[FeedbackMessage] = []

    async def send(self, feedback: FeedbackMessage) -> None:
        if self.should_fail:
            raise FeedbackDeliveryError("failed")
        self.messages.append(feedback)


@pytest.mark.asyncio
async def test_feedback_endpoint_sends_message() -> None:
    app = create_app()
    mailer = FakeFeedbackMailer()
    app.dependency_overrides[get_feedback_mailer] = lambda: mailer

    async with _client(app) as client:
        response = await client.post(
            "/api/v1/feedback",
            data={
                "name": "User",
                "email": "user@example.com",
                "message": "Please improve the pricing flow.",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert mailer.messages == [
        FeedbackMessage(
            name="User",
            email="user@example.com",
            message="Please improve the pricing flow.",
        )
    ]


@pytest.mark.asyncio
async def test_feedback_endpoint_sends_image_attachments() -> None:
    app = create_app()
    mailer = FakeFeedbackMailer()
    app.dependency_overrides[get_feedback_mailer] = lambda: mailer

    async with _client(app) as client:
        response = await client.post(
            "/api/v1/feedback",
            data={"message": "Screenshot attached."},
            files=[("images", ("bug.png", b"png-bytes", "image/png"))],
        )

    assert response.status_code == 200
    assert mailer.messages == [
        FeedbackMessage(
            name=None,
            email=None,
            message="Screenshot attached.",
            attachments=(
                FeedbackAttachment(
                    filename="bug.png",
                    content_type="image/png",
                    content=b"png-bytes",
                ),
            ),
        )
    ]


@pytest.mark.asyncio
async def test_feedback_endpoint_requires_delivery_config() -> None:
    app = create_app()
    app.dependency_overrides[get_feedback_mailer] = lambda: FakeFeedbackMailer(
        configured=False
    )

    async with _client(app) as client:
        response = await client.post(
            "/api/v1/feedback",
            data={"message": "Feedback text"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "FEEDBACK_UNAVAILABLE"


@pytest.mark.asyncio
async def test_feedback_endpoint_validates_message() -> None:
    async with _client(create_app()) as client:
        response = await client.post(
            "/api/v1/feedback",
            data={"email": "not-an-email", "message": "  "},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_feedback_endpoint_rejects_non_image_attachment() -> None:
    app = create_app()
    mailer = FakeFeedbackMailer()
    app.dependency_overrides[get_feedback_mailer] = lambda: mailer

    async with _client(app) as client:
        response = await client.post(
            "/api/v1/feedback",
            data={"message": "Unexpected attachment."},
            files=[("images", ("notes.txt", b"text", "text/plain"))],
        )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "FEEDBACK_ATTACHMENT_TYPE_UNSUPPORTED"
    assert mailer.messages == []


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    )
