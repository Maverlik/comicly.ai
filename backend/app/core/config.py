from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with safe local defaults."""

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
    database_direct_url: str | None = None
    migration_database_url: str | None = None
    cors_origins: str = ""
    full_page_generation_cost: int = 20
    scene_regeneration_cost: int = 4
    starter_coins: int = 100

    @model_validator(mode="after")
    def validate_coin_settings(self) -> Self:
        numeric_settings = {
            "full_page_generation_cost": self.full_page_generation_cost,
            "scene_regeneration_cost": self.scene_regeneration_cost,
            "starter_coins": self.starter_coins,
        }
        for name, value in numeric_settings.items():
            if value < 0:
                raise ValueError(f"{name} must be greater than or equal to zero")
        return self

    @property
    def alembic_database_url(self) -> str:
        return (
            self.migration_database_url or self.database_direct_url or self.database_url
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
