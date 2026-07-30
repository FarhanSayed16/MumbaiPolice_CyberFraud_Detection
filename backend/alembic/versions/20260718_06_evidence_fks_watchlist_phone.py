"""Phase 11-20 audit: evidence FKs + watchlist phone

Revision ID: 20260718_06
Revises: 9bf9fa817d4d
Create Date: 2026-07-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260718_06"
down_revision: Union[str, None] = "9bf9fa817d4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("watchlist_entries", sa.Column("phone", sa.String(length=50), nullable=True))
    op.create_index("ix_watchlist_entries_phone", "watchlist_entries", ["phone"], unique=False)

    op.add_column(
        "evidences",
        sa.Column("notice_id", sa.String(length=64), sa.ForeignKey("notices.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "evidences",
        sa.Column(
            "transaction_id",
            sa.String(length=64),
            sa.ForeignKey("transactions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_evidences_notice_id", "evidences", ["notice_id"], unique=False)
    op.create_index("ix_evidences_transaction_id", "evidences", ["transaction_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_evidences_transaction_id", table_name="evidences")
    op.drop_index("ix_evidences_notice_id", table_name="evidences")
    op.drop_column("evidences", "transaction_id")
    op.drop_column("evidences", "notice_id")
    op.drop_index("ix_watchlist_entries_phone", table_name="watchlist_entries")
    op.drop_column("watchlist_entries", "phone")
