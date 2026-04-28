# ruff: noqa: E501
"""phase6 generation idempotency

Revision ID: 0003_phase6_generation_idempotency
Revises: 0002_phase5_comic_persistence_fields
Create Date: 2026-04-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_phase6_generation_idempotency"
down_revision: str | None = "0002_phase5_comic_persistence_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("idempotency_key", sa.String(length=180), nullable=True),
    )
    op.create_unique_constraint(
        "uq_generation_jobs_idempotency_key",
        "generation_jobs",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_generation_jobs_idempotency_key",
        "generation_jobs",
        type_="unique",
    )
    op.drop_column("generation_jobs", "idempotency_key")
