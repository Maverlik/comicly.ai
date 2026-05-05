import base64
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import ApiError
from app.services.s3_storage import S3StorageService


class FakeS3Client:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict] = []

    def put_object(self, **kwargs):
        if self.error is not None:
            raise self.error
        self.calls.append(kwargs)
        return {"ETag": "fake"}


class FakeHttpClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    async def get(self, _url: str, **_kwargs):
        return self.response


def s3_settings(**overrides):
    defaults = {
        "s3_bucket": "comicly-generated",
        "s3_access_key_id": "access",
        "s3_secret_access_key": "secret",
        "s3_public_base_url": "https://cdn.example.com/comicly",
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


async def test_uploads_data_url_to_s3_with_public_url() -> None:
    client = FakeS3Client()
    service = S3StorageService(s3_settings(), client=client)
    data_url = "data:image/png;base64," + base64.b64encode(b"image").decode()

    result = await service.upload_generated_image(
        comic_id=uuid4(),
        page_id=uuid4(),
        image_source=data_url,
    )

    assert result.url.startswith("https://cdn.example.com/comicly/generated/comics/")
    assert result.storage_key.startswith("generated/comics/")
    assert result.content_type == "image/png"
    assert result.size == 5
    assert client.calls[0]["Bucket"] == "comicly-generated"
    assert client.calls[0]["Body"] == b"image"
    assert client.calls[0]["ContentType"] == "image/png"
    assert client.calls[0]["ACL"] == "public-read"


async def test_uploads_remote_image_to_s3_without_acl_when_disabled() -> None:
    client = FakeS3Client()
    http_client = FakeHttpClient(
        httpx.Response(
            200,
            content=b"webp",
            headers={"content-type": "image/webp; charset=binary"},
        )
    )
    service = S3StorageService(
        s3_settings(s3_public_read_acl=False),
        client=client,
        http_client=http_client,
    )

    result = await service.upload_generated_image(
        comic_id=uuid4(),
        page_id=uuid4(),
        image_source="https://example.com/image.webp",
    )

    assert result.content_type == "image/webp"
    assert result.storage_key.endswith(".webp")
    assert "ACL" not in client.calls[0]


async def test_missing_s3_config_is_typed() -> None:
    service = S3StorageService(
        s3_settings(s3_bucket=None),
    )

    with pytest.raises(ApiError) as exc_info:
        await service.upload_generated_image(
            comic_id=uuid4(),
            page_id=uuid4(),
            image_source="data:image/png;base64,aGVsbG8=",
        )

    assert exc_info.value.code == "STORAGE_NOT_CONFIGURED"
    assert "S3_BUCKET" in exc_info.value.message


async def test_s3_put_errors_are_typed() -> None:
    service = S3StorageService(
        s3_settings(),
        client=FakeS3Client(error=RuntimeError("boom")),
    )

    with pytest.raises(ApiError) as exc_info:
        await service.upload_generated_image(
            comic_id=uuid4(),
            page_id=uuid4(),
            image_source="data:image/png;base64,aGVsbG8=",
        )

    assert exc_info.value.code == "STORAGE_ERROR"
