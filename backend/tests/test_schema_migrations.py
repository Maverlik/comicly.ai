from pathlib import Path

import app.models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base

REQUIRED_PHASE2_TABLES = {
    "users",
    "provider_identities",
    "user_profiles",
    "user_sessions",
    "wallets",
    "wallet_transactions",
    "comics",
    "comic_scenes",
    "comic_pages",
    "generation_jobs",
    "coin_packages",
    "payments",
}


def test_alembic_env_imports_models_and_uses_migration_url() -> None:
    env_py = Path("alembic/env.py").read_text(encoding="utf-8")

    assert "import app.models" in env_py
    assert "settings.alembic_database_url" in env_py
    assert "settings.database_url" not in env_py


def test_settings_prefer_direct_url_for_migrations(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://runtime:secret@pooler.example.com/comicly",
    )
    monkeypatch.setenv(
        "DATABASE_DIRECT_URL",
        "postgresql+asyncpg://direct:secret@direct.example.com/comicly",
    )

    settings = Settings(_env_file=None)

    assert settings.alembic_database_url == settings.database_direct_url


def test_metadata_contains_all_phase2_tables_for_migration() -> None:
    assert REQUIRED_PHASE2_TABLES.issubset(Base.metadata.tables)


def test_initial_migration_mentions_all_phase2_tables() -> None:
    migration = Path("alembic/versions/0001_phase2_data_payment_schema.py").read_text(
        encoding="utf-8"
    )

    for table_name in REQUIRED_PHASE2_TABLES:
        assert f'"{table_name}"' in migration


def test_phase5_migration_mentions_comic_persistence_fields() -> None:
    migration = Path(
        "alembic/versions/0002_phase5_comic_persistence_fields.py"
    ).read_text(encoding="utf-8")

    for field_name in {
        "story",
        "characters",
        "style",
        "tone",
        "selected_model",
        "title",
        "description",
        "dialogue",
        "caption",
        "model",
        "coin_cost",
        "generated_at",
    }:
        assert f'"{field_name}"' in migration

    assert "ck_comic_pages_coin_cost_non_negative" in migration
