import pytest
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_auth_settings_have_safe_defaults_without_provider_secrets(monkeypatch) -> None:
    for name in (
        "SESSION_SECRET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "YANDEX_CLIENT_ID",
        "YANDEX_CLIENT_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.frontend_creator_url == "https://comicly-ai.ru/create.html"
    assert settings.oauth_callback_base_url is None
    assert settings.session_cookie_name == "comicly_session"
    assert settings.session_cookie_domain is None
    assert settings.session_cookie_secure is False
    assert settings.session_cookie_samesite == "lax"
    assert settings.session_lifetime_days == 30
    assert settings.google_client_id is None
    assert settings.yandex_client_secret is None


def test_auth_settings_support_production_cookie_overrides(monkeypatch) -> None:
    monkeypatch.setenv("SESSION_SECRET", "prod-secret")
    monkeypatch.setenv("FRONTEND_CREATOR_URL", "https://comicly-ai.ru/create.html")
    monkeypatch.setenv("OAUTH_CALLBACK_BASE_URL", "https://comicly-ai.ru")
    monkeypatch.setenv("SESSION_COOKIE_DOMAIN", ".comicly-ai.ru")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "none")
    monkeypatch.setenv("SESSION_LIFETIME_DAYS", "30")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-id")
    monkeypatch.setenv("YANDEX_CLIENT_SECRET", "yandex-secret")

    settings = Settings(_env_file=None)

    assert settings.session_secret == "prod-secret"
    assert settings.oauth_callback_base_url == "https://comicly-ai.ru"
    assert settings.session_cookie_domain == ".comicly-ai.ru"
    assert settings.session_cookie_secure is True
    assert settings.session_cookie_samesite == "none"
    assert settings.session_lifetime_days == 30
    assert settings.google_client_id == "google-id"
    assert settings.yandex_client_secret == "yandex-secret"


def test_production_requires_explicit_session_secret(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SESSION_SECRET", raising=False)

    with pytest.raises(ValueError, match="SESSION_SECRET"):
        Settings(_env_file=None)


def test_samesite_none_requires_secure_cookie() -> None:
    with pytest.raises(ValueError, match="requires secure cookies"):
        Settings(
            _env_file=None,
            session_cookie_samesite="none",
            session_cookie_secure=False,
        )


def test_create_app_adds_oauth_state_session_middleware(monkeypatch) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")

    app = create_app()

    session_middleware = [
        middleware
        for middleware in app.user_middleware
        if isinstance(middleware, Middleware)
        and middleware.cls.__name__ == "SessionMiddleware"
        and middleware.kwargs["session_cookie"] == "comicly_oauth_state"
    ]
    assert session_middleware


def test_create_app_configures_credentialed_cors_without_wildcard(monkeypatch) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://comicly-ai.ru,*",
    )

    app = create_app()

    cors_middleware = [
        middleware
        for middleware in app.user_middleware
        if isinstance(middleware, Middleware) and middleware.cls is CORSMiddleware
    ]
    assert cors_middleware
    assert cors_middleware[0].kwargs["allow_origins"] == [
        "https://comicly-ai.ru",
    ]
    assert cors_middleware[0].kwargs["allow_credentials"] is True
