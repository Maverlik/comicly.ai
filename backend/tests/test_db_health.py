import pytest

from app.core.errors import ApiError
from app.db import health


class FailingEngine:
    def connect(self):
        raise OSError("database unavailable")


@pytest.mark.anyio
async def test_database_ready_wraps_connection_errors(monkeypatch) -> None:
    monkeypatch.setattr(health, "engine", FailingEngine())

    with pytest.raises(ApiError) as exc_info:
        await health.check_database_ready()

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "DATABASE_UNAVAILABLE"
    assert exc_info.value.message == "Database is not ready"
