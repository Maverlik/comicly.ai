# ruff: noqa: E501
"""phase5 comic persistence fields

Revision ID: 0002_phase5_comic_persistence_fields
Revises: 0001_phase2_data_payment_schema
Create Date: 2026-04-27 20:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_phase5_comic_persistence_fields"
down_revision: str | None = "0001_phase2_data_payment_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("comics", sa.Column("story", sa.Text(), nullable=True))
    op.add_column("comics", sa.Column("characters", sa.Text(), nullable=True))
    op.add_column("comics", sa.Column("style", sa.String(length=120), nullable=True))
    op.add_column("comics", sa.Column("tone", sa.String(length=120), nullable=True))
    op.add_column(
        "comics",
        sa.Column("selected_model", sa.String(length=160), nullable=True),
    )

    op.add_column(
        "comic_scenes",
        sa.Column("title", sa.String(length=200), nullable=True),
    )
    op.add_column("comic_scenes", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("comic_scenes", sa.Column("dialogue", sa.Text(), nullable=True))
    op.add_column("comic_scenes", sa.Column("caption", sa.Text(), nullable=True))

    op.add_column(
        "comic_pages",
        sa.Column("model", sa.String(length=160), nullable=True),
    )
    op.add_column("comic_pages", sa.Column("coin_cost", sa.Integer(), nullable=True))
    op.add_column(
        "comic_pages",
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_comic_pages_coin_cost_non_negative",
        "comic_pages",
        "coin_cost IS NULL OR coin_cost >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_comic_pages_coin_cost_non_negative",
        "comic_pages",
        type_="check",
    )
    op.drop_column("comic_pages", "generated_at")
    op.drop_column("comic_pages", "coin_cost")
    op.drop_column("comic_pages", "model")

    op.drop_column("comic_scenes", "caption")
    op.drop_column("comic_scenes", "dialogue")
    op.drop_column("comic_scenes", "description")
    op.drop_column("comic_scenes", "title")

    op.drop_column("comics", "selected_model")
    op.drop_column("comics", "tone")
    op.drop_column("comics", "style")
    op.drop_column("comics", "characters")
    op.drop_column("comics", "story")
