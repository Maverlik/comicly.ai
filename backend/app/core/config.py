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
    openrouter_api_key: str | None = None
    openrouter_site_url: str = "https://comicly.ai"
    openrouter_app_name: str = "comicly.ai"
    openrouter_default_image_model: str = "bytedance-seed/seedream-4.5"
    openrouter_default_text_model: str = "google/gemini-2.5-flash"
    openrouter_allowed_image_models: str = (
        "bytedance-seed/seedream-4.5,"
        "google/gemini-3-pro-image-preview,"
        "openai/gpt-5.4-image-2"
    )
    openrouter_image_aspect_ratio: str = "1:1"
    openrouter_request_timeout_seconds: float = 60.0
    blob_read_write_token: str | None = None
    security_headers_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 60
    yookassa_shop_id: str | None = None
    yookassa_api_key: str | None = None
    yookassa_api_url: str = "https://api.yookassa.ru/v3"
    yookassa_request_timeout_seconds: float = 20.0
    yookassa_return_url: str = "https://comicly.ai/pricing.html?payment=return"
    yookassa_webhook_ip_allowlist: str = (
        "185.71.76.0/27,"
        "185.71.77.0/27,"
        "77.75.153.0/25,"
        "77.75.156.11,"
        "77.75.156.35,"
        "77.75.154.128/25,"
        "2a02:5180::/32"
    )
    yookassa_webhook_ip_check_enabled: bool = True

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
        if self.openrouter_request_timeout_seconds <= 0:
            raise ValueError(
                "OPENROUTER_REQUEST_TIMEOUT_SECONDS must be greater than zero"
            )
        if self.rate_limit_window_seconds <= 0:
            raise ValueError("RATE_LIMIT_WINDOW_SECONDS must be greater than zero")
        if self.rate_limit_max_requests <= 0:
            raise ValueError("RATE_LIMIT_MAX_REQUESTS must be greater than zero")
        if self.yookassa_request_timeout_seconds <= 0:
            raise ValueError(
                "YOOKASSA_REQUEST_TIMEOUT_SECONDS must be greater than zero"
            )
        if not self.openrouter_allowed_image_model_list:
            raise ValueError("OPENROUTER_ALLOWED_IMAGE_MODELS must not be empty")
        if (
            self.openrouter_default_image_model
            not in self.openrouter_allowed_image_model_list
        ):
            raise ValueError(
                "OPENROUTER_DEFAULT_IMAGE_MODEL must be present in "
                "OPENROUTER_ALLOWED_IMAGE_MODELS"
            )
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
    def openrouter_allowed_image_model_list(self) -> list[str]:
        return [
            model.strip()
            for model in self.openrouter_allowed_image_models.split(",")
            if model.strip()
        ]

    @property
    def openrouter_allowed_image_model_set(self) -> set[str]:
        return set(self.openrouter_allowed_image_model_list)

    @property
    def yookassa_webhook_ip_allowlist_entries(self) -> list[str]:
        return [
            entry.strip()
            for entry in self.yookassa_webhook_ip_allowlist.split(",")
            if entry.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
