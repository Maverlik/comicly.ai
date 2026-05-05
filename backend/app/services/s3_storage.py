from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.services.image_storage_common import (
    StoredImage,
    decode_data_url,
    generated_image_key,
)


class S3StorageService:
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
    ) -> StoredImage:
        self._require_config()
        image_bytes, content_type = await self._read_image_source(image_source)
        storage_key = generated_image_key(
            comic_id=comic_id,
            page_id=page_id,
            content_type=content_type,
        )
        client = self._client or _build_s3_client(self._settings)
        put_kwargs = {
            "Bucket": self._settings.s3_bucket,
            "Key": storage_key,
            "Body": image_bytes,
            "ContentType": content_type,
        }
        if self._settings.s3_public_read_acl:
            put_kwargs["ACL"] = "public-read"

        try:
            await asyncio.to_thread(client.put_object, **put_kwargs)
        except Exception as exc:
            raise ApiError(
                status_code=502,
                code="STORAGE_ERROR",
                message="Generated image could not be stored.",
            ) from exc

        return StoredImage(
            url=_public_url(self._settings, storage_key),
            storage_key=storage_key,
            content_type=content_type,
            size=len(image_bytes),
        )

    def _require_config(self) -> None:
        if self._client is not None:
            return
        required = {
            "S3_BUCKET": self._settings.s3_bucket,
            "S3_ACCESS_KEY_ID": self._settings.s3_access_key_id,
            "S3_SECRET_ACCESS_KEY": self._settings.s3_secret_access_key,
            "S3_PUBLIC_BASE_URL": self._settings.s3_public_base_url,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ApiError(
                status_code=503,
                code="STORAGE_NOT_CONFIGURED",
                message=f"S3 storage is not configured: {', '.join(missing)}.",
            )

    async def _read_image_source(self, image_source: str) -> tuple[bytes, str]:
        if image_source.startswith("data:"):
            return decode_data_url(image_source)
        if image_source.startswith(("http://", "https://")):
            return await self._fetch_remote_image(image_source)
        raise ApiError(
            status_code=400,
            code="STORAGE_SOURCE_INVALID",
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
                code="STORAGE_SOURCE_FETCH_FAILED",
                message="Generated image could not be fetched.",
            ) from exc
        if response.status_code >= 400:
            raise ApiError(
                status_code=502,
                code="STORAGE_SOURCE_FETCH_FAILED",
                message="Generated image fetch returned an error.",
            )
        content_type = response.headers.get("content-type", "image/png").split(";")[0]
        return response.content, content_type or "image/png"


def _build_s3_client(settings: Settings) -> Any:
    import boto3
    from botocore.config import Config

    config = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"},
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        region_name=settings.s3_region or None,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=config,
    )


def _public_url(settings: Settings, storage_key: str) -> str:
    return f"{settings.s3_public_base_url.rstrip('/')}/{storage_key.lstrip('/')}"
