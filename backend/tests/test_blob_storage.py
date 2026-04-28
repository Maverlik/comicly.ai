import base64
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import ApiError
from app.services.blob_storage import BlobStorageService


class FakeBlobClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def put(self, pathname, body, **kwargs):
        self.calls.append({"pathname": pathname, "body": body, **kwargs})
        return SimpleNamespace(
            url=f"https://blob.example/{pathname}",
            pathname=pathname,
        )


class FakeHttpClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    async def get(self, _url: str, **_kwargs):
        return self.response


async def test_uploads_data_url_to_blob_with_generated_path(monkeypatch) -> None:
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "blob-secret")
    client = FakeBlobClient()
    service = BlobStorageService(Settings(_env_file=None), client=client)
    data_url = "data:image/png;base64," + base64.b64encode(b"image").decode()

    result = await service.upload_generated_image(
        comic_id=uuid4(),
        page_id=uuid4(),
        image_source=data_url,
    )

    assert result.url.startswith("https://blob.example/generated/comics/")
    assert result.storage_key.startswith("generated/comics/")
    assert result.content_type == "image/png"
    assert result.size == 5
    assert client.calls[0]["body"] == b"image"
    assert client.calls[0]["access"] == "public"
    assert client.calls[0]["content_type"] == "image/png"


async def test_uploads_remote_image_bytes(monkeypatch) -> None:
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "blob-secret")
    client = FakeBlobClient()
    http_client = FakeHttpClient(
        httpx.Response(
            200,
            content=b"webp",
            headers={"content-type": "image/webp; charset=binary"},
        )
    )
    service = BlobStorageService(
        Settings(_env_file=None),
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
    assert client.calls[0]["body"] == b"webp"


async def test_missing_blob_token_is_typed(monkeypatch) -> None:
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    service = BlobStorageService(Settings(_env_file=None))

    with pytest.raises(ApiError) as exc_info:
        await service.upload_generated_image(
            comic_id=uuid4(),
            page_id=uuid4(),
            image_source="data:image/png;base64,aGVsbG8=",
        )

    assert exc_info.value.code == "BLOB_STORAGE_NOT_CONFIGURED"


async def test_invalid_data_url_is_typed(monkeypatch) -> None:
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "blob-secret")
    service = BlobStorageService(Settings(_env_file=None), client=FakeBlobClient())

    with pytest.raises(ApiError) as exc_info:
        await service.upload_generated_image(
            comic_id=uuid4(),
            page_id=uuid4(),
            image_source="data:image/png;base64,not-valid!",
        )

    assert exc_info.value.code == "BLOB_SOURCE_INVALID"
