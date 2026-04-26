import app.models  # noqa: F401
from app.db.base import Base


def constraint_names(table_name: str) -> set[str]:
    return {
        constraint.name
        for constraint in Base.metadata.tables[table_name].constraints
        if constraint.name
    }


def foreign_key_targets(table_name: str) -> set[str]:
    return {
        f"{fk.column.table.name}.{fk.column.name}"
        for fk in Base.metadata.tables[table_name].foreign_keys
    }


def test_provider_identity_uniqueness_constraint_exists() -> None:
    assert "uq_provider_identities_provider_user" in constraint_names(
        "provider_identities"
    )


def test_wallet_constraints_exist() -> None:
    assert "ck_wallets_balance_non_negative" in constraint_names("wallets")
    assert "ck_wallet_transactions_amount_non_zero" in constraint_names(
        "wallet_transactions"
    )
    assert "idempotency_key" in Base.metadata.tables["wallet_transactions"].columns


def test_payment_idempotency_constraints_exist() -> None:
    names = constraint_names("payments")

    assert "uq_payments_provider_payment" in names
    assert any(
        {"idempotency_key"} == {column.name for column in constraint.columns}
        for constraint in Base.metadata.tables["payments"].constraints
    )
    assert any(
        {"webhook_event_id"} == {column.name for column in constraint.columns}
        for constraint in Base.metadata.tables["payments"].constraints
    )


def test_comic_page_relationships_prevent_orphans_and_cross_scene_links() -> None:
    names = constraint_names("comic_pages")
    targets = foreign_key_targets("comic_pages")

    assert "fk_comic_pages_scene_same_comic" in names
    assert "comics.id" in targets
    assert "comic_scenes.id" in targets
    assert "comic_scenes.comic_id" in targets
