import app.models  # noqa: F401
from app.db.base import Base


def test_phase2_tables_are_registered_in_metadata() -> None:
    expected_tables = {
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

    assert expected_tables.issubset(Base.metadata.tables)


def test_identity_wallet_generation_and_payment_columns_exist() -> None:
    tables = Base.metadata.tables

    assert {"provider", "provider_user_id", "user_id"}.issubset(
        tables["provider_identities"].columns.keys()
    )
    assert {"balance", "user_id"}.issubset(tables["wallets"].columns.keys())
    assert {"amount", "balance_after", "idempotency_key"}.issubset(
        tables["wallet_transactions"].columns.keys()
    )
    assert {"status", "job_type", "coin_cost", "request_payload"}.issubset(
        tables["generation_jobs"].columns.keys()
    )
    assert {"code", "coin_amount", "amount", "currency", "active"}.issubset(
        tables["coin_packages"].columns.keys()
    )
    assert {
        "status",
        "provider_payment_id",
        "provider_checkout_id",
        "webhook_event_id",
        "idempotency_key",
    }.issubset(tables["payments"].columns.keys())


def test_representative_constraints_are_present() -> None:
    tables = Base.metadata.tables

    provider_constraints = {
        constraint.name for constraint in tables["provider_identities"].constraints
    }
    wallet_constraints = {
        constraint.name for constraint in tables["wallets"].constraints
    }
    package_constraints = {
        constraint.name for constraint in tables["coin_packages"].constraints
    }

    assert "uq_provider_identities_provider_user" in provider_constraints
    assert "ck_wallets_balance_non_negative" in wallet_constraints
    assert "ck_coin_packages_coin_amount_positive" in package_constraints
