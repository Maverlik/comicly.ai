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
    assert settings.openrouter_api_key is None
    assert settings.openrouter_default_image_model in (
        settings.openrouter_allowed_image_model_set
    )
    assert settings.blob_read_write_token is None


def test_settings_support_phase2_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://runtime:secret@pooler.example.com/comicly",
    )
    monkeypatch.setenv(
        "DATABASE_DIRECT_URL",
        "postgresql+asyncpg://direct:secret@direct.example.com/comicly",
    )
    monkeypatch.setenv("CORS_ORIGINS", "https://comicly-ai.ru")
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
    assert settings.cors_origins == "https://comicly-ai.ru"
    assert settings.cors_origin_list == ["https://comicly-ai.ru"]
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


def test_settings_support_phase6_generation_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "phase-6-secret")
    monkeypatch.setenv("OPENROUTER_SITE_URL", "https://comicly-ai.ru")
    monkeypatch.setenv("OPENROUTER_APP_NAME", "Comicly")
    monkeypatch.setenv("OPENROUTER_DEFAULT_IMAGE_MODEL", "allowed/model-a")
    monkeypatch.setenv("OPENROUTER_DEFAULT_TEXT_MODEL", "text/model")
    monkeypatch.setenv(
        "OPENROUTER_ALLOWED_IMAGE_MODELS",
        " allowed/model-a,allowed/model-b ,, ",
    )
    monkeypatch.setenv("OPENROUTER_IMAGE_ASPECT_RATIO", "16:9")
    monkeypatch.setenv("OPENROUTER_REQUEST_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "blob-secret")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "phase-3-secret")
    monkeypatch.setenv("STORAGE_SECRET_ACCESS_KEY", "not-used-in-phase-1")

    settings = Settings(_env_file=None)

    assert settings.openrouter_api_key == "phase-6-secret"
    assert settings.openrouter_site_url == "https://comicly-ai.ru"
    assert settings.openrouter_app_name == "Comicly"
    assert settings.openrouter_default_image_model == "allowed/model-a"
    assert settings.openrouter_default_text_model == "text/model"
    assert settings.openrouter_allowed_image_model_list == [
        "allowed/model-a",
        "allowed/model-b",
    ]
    assert settings.openrouter_allowed_image_model_set == {
        "allowed/model-a",
        "allowed/model-b",
    }
    assert settings.openrouter_image_aspect_ratio == "16:9"
    assert settings.openrouter_request_timeout_seconds == 45
    assert settings.blob_read_write_token == "blob-secret"
    assert settings.google_client_secret == "phase-3-secret"
    assert not hasattr(settings, "storage_secret_access_key")


def test_default_image_model_must_be_allowed(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_DEFAULT_IMAGE_MODEL", "blocked/model")
    monkeypatch.setenv("OPENROUTER_ALLOWED_IMAGE_MODELS", "allowed/model")

    try:
        Settings(_env_file=None)
    except ValueError as exc:
        assert "OPENROUTER_DEFAULT_IMAGE_MODEL" in str(exc)
    else:
        raise AssertionError("expected invalid model config to fail")


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
