from __future__ import annotations

import base64
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.core.errors import ApiError


@dataclass(frozen=True)
class StoredImage:
    url: str
    storage_key: str
    content_type: str
    size: int


def decode_data_url(value: str) -> tuple[bytes, str]:
    header, separator, encoded = value.partition(",")
    if not separator or ";base64" not in header:
        raise ApiError(
            status_code=400,
            code="STORAGE_SOURCE_INVALID",
            message="Generated image data URL is invalid.",
        )
    content_type = header.removeprefix("data:").split(";")[0] or "image/png"
    try:
        return base64.b64decode(encoded, validate=True), content_type
    except ValueError as exc:
        raise ApiError(
            status_code=400,
            code="STORAGE_SOURCE_INVALID",
            message="Generated image data URL is invalid.",
        ) from exc


def generated_image_key(
    *,
    comic_id: UUID,
    page_id: UUID,
    content_type: str,
) -> str:
    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(content_type, "png")
    return f"generated/comics/{comic_id}/pages/{page_id}-{uuid4()}.{extension}"
