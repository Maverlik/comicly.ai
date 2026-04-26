from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings


def build_async_engine(settings: Settings):
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        poolclass=NullPool,
    )


settings = get_settings()

engine = build_async_engine(settings)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
