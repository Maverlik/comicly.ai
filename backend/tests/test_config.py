from app.core.config import Settings
from app.main import create_app


def test_settings_have_safe_phase1_defaults_without_future_env_vars(
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
        "STARTER_COINS",
    ]
    for name in future_env_vars:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "Comicly API"
    assert settings.app_env == "local"
    assert settings.app_debug is False
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_settings_ignore_later_phase_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-used-in-phase-1")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "not-used-in-phase-1")
    monkeypatch.setenv("STARTER_COINS", "250")

    settings = Settings(_env_file=None)

    assert not hasattr(settings, "openrouter_api_key")
    assert not hasattr(settings, "google_client_secret")
    assert not hasattr(settings, "starter_coins")


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
