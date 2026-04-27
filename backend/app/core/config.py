from functools import lru_cache
from typing import Self

from pydantic import field_validator, model_validator
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
    session_secret: str = "change-me-in-production"
    frontend_creator_url: str = "https://comicly.ai/create.html"
    session_cookie_name: str = "comicly_session"
    session_cookie_domain: str | None = None
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_lifetime_days: int = 30
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_server_metadata_url: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    yandex_client_id: str | None = None
    yandex_client_secret: str | None = None
    yandex_authorize_url: str = "https://oauth.yandex.com/authorize"
    yandex_access_token_url: str = "https://oauth.yandex.com/token"
    yandex_userinfo_endpoint: str = "https://login.yandex.ru/info"

    @model_validator(mode="after")
    def validate_coin_settings(self) -> Self:
        numeric_settings = {
            "full_page_generation_cost": self.full_page_generation_cost,
            "scene_regeneration_cost": self.scene_regeneration_cost,
            "starter_coins": self.starter_coins,
            "session_lifetime_days": self.session_lifetime_days,
        }
        for name, value in numeric_settings.items():
            if value <= 0 and name == "session_lifetime_days":
                raise ValueError(f"{name} must be greater than zero")
            if value < 0 and name != "session_lifetime_days":
                raise ValueError(f"{name} must be greater than or equal to zero")

        if self.is_production and self.session_secret == "change-me-in-production":
            raise ValueError("SESSION_SECRET must be set outside local development")
        if self.session_cookie_samesite == "none" and not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SAMESITE=none requires secure cookies")
        return self

    @field_validator("session_cookie_samesite")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("session_cookie_samesite must be lax, strict, or none")
        return normalized

    @property
    def alembic_database_url(self) -> str:
        return (
            self.migration_database_url or self.database_direct_url or self.database_url
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip() and origin.strip() != "*"
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
