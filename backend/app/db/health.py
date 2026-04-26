from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import ApiError
from app.db.session import engine


async def check_database_ready() -> None:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApiError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="Database is not ready",
        ) from exc

