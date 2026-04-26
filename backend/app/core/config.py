from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Phase 1 runtime settings with safe local defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "Comicly API"
    app_env: str = "local"
    app_debug: bool = False
    database_url: str = "postgresql+asyncpg://comicly:comicly@localhost:5432/comicly"


@lru_cache
def get_settings() -> Settings:
    return Settings()
