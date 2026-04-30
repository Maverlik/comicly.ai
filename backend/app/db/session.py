from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings


def build_async_engine(settings: Settings):
    engine_options = {
        "pool_pre_ping": True,
        "pool_size": 1,
        "max_overflow": 2,
        "pool_recycle": 300,
    }
    if settings.database_url.startswith("postgresql+asyncpg://"):
        engine_options["connect_args"] = {
            # Transaction poolers such as Supabase/PgBouncer cannot reliably
            # reuse asyncpg prepared statements across backend connections.
            "statement_cache_size": 0,
        }

    return create_async_engine(
        settings.database_url,
        **engine_options,
    )


settings = get_settings()

engine = build_async_engine(settings)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
