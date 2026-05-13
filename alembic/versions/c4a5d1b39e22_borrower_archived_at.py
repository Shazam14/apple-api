"""borrower archived_at

Revision ID: c4a5d1b39e22
Revises: b2f4c8a91d33
Create Date: 2026-05-13 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a5d1b39e22"
down_revision: Union[str, None] = "b2f4c8a91d33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "borrowers",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("borrowers", "archived_at")
