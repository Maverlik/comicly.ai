from app.core.config import Settings
from app.db.session import build_async_engine
from app.main import create_app


def test_settings_have_safe_defaults_without_future_env_vars(
    monkeypatch,
) -> None:
    future_env_vars = [
        "SESSION_SECRET",
        "APP_URL",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "YANDEX_CLIENT_ID",
        "YANDEX_CLIENT_SECRET",
        "OPENROUTER_API_KEY",
        "STORAGE_SECRET_ACCESS_KEY",
    ]
    for name in future_env_vars:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "Comicly API"
    assert settings.app_env == "local"
    assert settings.app_debug is False
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.alembic_database_url == settings.database_url
    assert settings.full_page_generation_cost == 20
    assert settings.scene_regeneration_cost == 4
    assert settings.starter_coins == 100
    assert settings.cors_origins == ""
    assert settings.cors_origin_list == []


def test_settings_support_phase2_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://runtime:secret@pooler.example.com/comicly",
    )
    monkeypatch.setenv(
        "DATABASE_DIRECT_URL",
        "postgresql+asyncpg://direct:secret@direct.example.com/comicly",
    )
    monkeypatch.setenv("CORS_ORIGINS", "https://comicly.ai, https://www.comicly.ai")
    monkeypatch.setenv("FULL_PAGE_GENERATION_COST", "30")
    monkeypatch.setenv("SCENE_REGENERATION_COST", "6")
    monkeypatch.setenv("STARTER_COINS", "250")

    settings = Settings(_env_file=None)

    assert settings.database_url == (
        "postgresql+asyncpg://runtime:secret@pooler.example.com/comicly"
    )
    assert settings.database_direct_url == (
        "postgresql+asyncpg://direct:secret@direct.example.com/comicly"
    )
    assert settings.alembic_database_url == settings.database_direct_url
    assert settings.cors_origins == "https://comicly.ai, https://www.comicly.ai"
    assert settings.cors_origin_list == ["https://comicly.ai", "https://www.comicly.ai"]
    assert settings.full_page_generation_cost == 30
    assert settings.scene_regeneration_cost == 6
    assert settings.starter_coins == 250


def test_migration_database_url_has_priority_over_direct_url(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://runtime:secret@pooler.example.com/comicly",
    )
    monkeypatch.setenv(
        "DATABASE_DIRECT_URL",
        "postgresql+asyncpg://direct:secret@direct.example.com/comicly",
    )
    monkeypatch.setenv(
        "MIGRATION_DATABASE_URL",
        "postgresql+asyncpg://migration:secret@direct.example.com/comicly",
    )

    settings = Settings(_env_file=None)

    assert settings.alembic_database_url == (
        "postgresql+asyncpg://migration:secret@direct.example.com/comicly"
    )


def test_runtime_engine_uses_runtime_database_url_not_direct_url(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://runtime:secret@pooler.example.com/comicly",
    )
    monkeypatch.setenv(
        "DATABASE_DIRECT_URL",
        "postgresql+asyncpg://direct:secret@direct.example.com/comicly",
    )
    settings = Settings(_env_file=None)

    engine = build_async_engine(settings)

    assert engine.url.render_as_string(hide_password=False) == settings.database_url
    assert (
        engine.url.render_as_string(hide_password=False) != settings.database_direct_url
    )


def test_settings_ignore_unimplemented_secret_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-used-in-phase-1")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "not-used-in-phase-1")
    monkeypatch.setenv("STORAGE_SECRET_ACCESS_KEY", "not-used-in-phase-1")

    settings = Settings(_env_file=None)

    assert not hasattr(settings, "openrouter_api_key")
    assert not hasattr(settings, "google_client_secret")
    assert not hasattr(settings, "storage_secret_access_key")


def test_create_app_starts_without_later_phase_env_vars(monkeypatch) -> None:
    for name in (
        "SESSION_SECRET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "YANDEX_CLIENT_ID",
        "YANDEX_CLIENT_SECRET",
        "OPENROUTER_API_KEY",
        "STARTER_COINS",
    ):
        monkeypatch.delenv(name, raising=False)

    app = create_app()

    assert app.title == "Comicly API"
