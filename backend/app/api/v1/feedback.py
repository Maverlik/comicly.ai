from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ValidationError, field_validator

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.services.feedback import (
    FeedbackAttachment,
    FeedbackDeliveryError,
    FeedbackMailer,
    FeedbackMessage,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])
SettingsDep = Annotated[Settings, Depends(get_settings)]
MAX_ATTACHMENT_COUNT = 3
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


def get_feedback_mailer(settings: SettingsDep) -> FeedbackMailer:
    return FeedbackMailer(settings)


FeedbackMailerDep = Annotated[FeedbackMailer, Depends(get_feedback_mailer)]


class FeedbackRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    message: str

    @field_validator("name", "email", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "@" not in value or len(value) > 254:
            raise ValueError("email must be a valid email address")
        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("message must contain at least 3 characters")
        if len(normalized) > 4000:
            raise ValueError("message must contain at most 4000 characters")
        return normalized


class FeedbackResponse(BaseModel):
    ok: bool


@router.post("", response_model=FeedbackResponse)
async def send_feedback(
    mailer: FeedbackMailerDep,
    name: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    message: Annotated[str, Form()] = "",
    images: Annotated[list[UploadFile] | None, File()] = None,
) -> FeedbackResponse:
    try:
        payload = FeedbackRequest(name=name, email=email, message=message)
    except ValidationError as exc:
        raise ApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Invalid request.",
        ) from exc
    if not mailer.is_configured:
        raise ApiError(
            status_code=503,
            code="FEEDBACK_UNAVAILABLE",
            message="Feedback email delivery is not configured.",
        )

    attachments = await _read_image_attachments(images or [])
    try:
        await mailer.send(
            FeedbackMessage(
                name=payload.name,
                email=payload.email,
                message=payload.message,
                attachments=tuple(attachments),
            )
        )
    except FeedbackDeliveryError as exc:
        raise ApiError(
            status_code=502,
            code="FEEDBACK_DELIVERY_FAILED",
            message="Feedback email delivery failed.",
        ) from exc

    return FeedbackResponse(ok=True)


async def _read_image_attachments(
    images: list[UploadFile],
) -> list[FeedbackAttachment]:
    if len(images) > MAX_ATTACHMENT_COUNT:
        raise ApiError(
            status_code=413,
            code="FEEDBACK_TOO_MANY_ATTACHMENTS",
            message="Too many image attachments.",
        )

    attachments: list[FeedbackAttachment] = []
    total_size = 0
    for image in images:
        content_type = (image.content_type or "").lower()
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ApiError(
                status_code=415,
                code="FEEDBACK_ATTACHMENT_TYPE_UNSUPPORTED",
                message="Feedback attachments must be images.",
            )

        content = await image.read()
        size = len(content)
        total_size += size
        if size > MAX_ATTACHMENT_BYTES or total_size > MAX_TOTAL_ATTACHMENT_BYTES:
            raise ApiError(
                status_code=413,
                code="FEEDBACK_ATTACHMENT_TOO_LARGE",
                message="Feedback image attachments are too large.",
            )
        if size == 0:
            continue

        attachments.append(
            FeedbackAttachment(
                filename=(image.filename or "feedback-image").strip()
                or "feedback-image",
                content_type=content_type,
                content=content,
            )
        )
    return attachments
