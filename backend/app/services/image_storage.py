from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.services.s3_storage import S3StorageService


def build_image_storage(settings: Settings) -> Any:
    return S3StorageService(settings)
