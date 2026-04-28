from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import httpx

from app.core.config import Settings
from app.core.errors import ApiError


@dataclass(frozen=True)
class StoredBlob:
    url: str
    storage_key: str
    content_type: str
    size: int


class BlobStorageService:
    def __init__(
        self,
        settings: Settings,
        *,
        client: Any | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client
        self._http_client = http_client

    async def upload_generated_image(
        self,
        *,
        comic_id: UUID,
        page_id: UUID,
        image_source: str,
    ) -> StoredBlob:
        if not self._settings.blob_read_write_token and self._client is None:
            raise ApiError(
                status_code=503,
                code="BLOB_STORAGE_NOT_CONFIGURED",
                message="Blob storage token is not configured.",
            )

        image_bytes, content_type = await self._read_image_source(image_source)
        storage_key = _generated_image_key(
            comic_id=comic_id,
            page_id=page_id,
            content_type=content_type,
        )
        client = self._client or _build_blob_client(self._settings)
        try:
            blob = await client.put(
                storage_key,
                image_bytes,
                access="public",
                content_type=content_type,
            )
        except TypeError:
            blob = await client.put(storage_key, image_bytes, access="public")
        except Exception as exc:
            raise ApiError(
                status_code=502,
                code="BLOB_STORAGE_ERROR",
                message="Generated image could not be stored.",
            ) from exc

        return StoredBlob(
            url=_blob_attr(blob, "url"),
            storage_key=_blob_attr(blob, "pathname", fallback=storage_key),
            content_type=content_type,
            size=len(image_bytes),
        )

    async def _read_image_source(self, image_source: str) -> tuple[bytes, str]:
        if image_source.startswith("data:"):
            return _decode_data_url(image_source)
        if image_source.startswith(("http://", "https://")):
            return await self._fetch_remote_image(image_source)
        raise ApiError(
            status_code=400,
            code="BLOB_SOURCE_INVALID",
            message="Generated image source is invalid.",
        )

    async def _fetch_remote_image(self, url: str) -> tuple[bytes, str]:
        try:
            if self._http_client is not None:
                response = await self._http_client.get(url, timeout=20.0)
            else:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.get(url)
        except httpx.HTTPError as exc:
            raise ApiError(
                status_code=502,
                code="BLOB_SOURCE_FETCH_FAILED",
                message="Generated image could not be fetched.",
            ) from exc
        if response.status_code >= 400:
            raise ApiError(
                status_code=502,
                code="BLOB_SOURCE_FETCH_FAILED",
                message="Generated image fetch returned an error.",
            )
        content_type = response.headers.get("content-type", "image/png").split(";")[0]
        return response.content, content_type or "image/png"


def _decode_data_url(value: str) -> tuple[bytes, str]:
    header, separator, encoded = value.partition(",")
    if not separator or ";base64" not in header:
        raise ApiError(
            status_code=400,
            code="BLOB_SOURCE_INVALID",
            message="Generated image data URL is invalid.",
        )
    content_type = header.removeprefix("data:").split(";")[0] or "image/png"
    try:
        return base64.b64decode(encoded, validate=True), content_type
    except ValueError as exc:
        raise ApiError(
            status_code=400,
            code="BLOB_SOURCE_INVALID",
            message="Generated image data URL is invalid.",
        ) from exc


def _generated_image_key(
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


def _build_blob_client(settings: Settings) -> Any:
    from vercel.blob import AsyncBlobClient

    return AsyncBlobClient(token=settings.blob_read_write_token)


def _blob_attr(blob: Any, attr: str, *, fallback: str | None = None) -> str:
    if isinstance(blob, dict):
        value = blob.get(attr) or fallback
    else:
        value = getattr(blob, attr, None) or fallback
    if not value:
        raise ApiError(
            status_code=502,
            code="BLOB_STORAGE_ERROR",
            message="Blob storage response was invalid.",
        )
    return str(value)
