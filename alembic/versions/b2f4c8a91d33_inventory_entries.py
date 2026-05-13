"""inventory_entries

Revision ID: b2f4c8a91d33
Revises: 8d6fa7a11c42
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f4c8a91d33"
down_revision: Union[str, None] = "8d6fa7a11c42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_username", sa.String(length=64), nullable=False),
        sa.Column(
            "category",
            sa.Enum("EXPENSE", "THAN_EXTRA", name="inventory_category"),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inventory_entries_owner_username"),
        "inventory_entries",
        ["owner_username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_entries_owner_username"), table_name="inventory_entries")
    op.drop_table("inventory_entries")
    sa.Enum(name="inventory_category").drop(op.get_bind(), checkfirst=True)
