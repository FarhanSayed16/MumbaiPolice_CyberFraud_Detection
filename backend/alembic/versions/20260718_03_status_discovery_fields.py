"""Align case statuses to master plan + discovery intake fields (audit H6/H7).

Revision ID: 20260718_03
Revises: 20260718_02
Create Date: 2026-07-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260718_03"
down_revision: Union[str, None] = "20260718_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STATUS_MAP = {
    "intake": "intake_complete",
    "triage": "tracing",
    "investigating": "tracing",
    "freeze_confirmed": "action_taken",
    "partial_freeze": "partially_recovered",
    "merged": "closed",
}


def upgrade() -> None:
    for old, new in STATUS_MAP.items():
        op.execute(sa.text(f"UPDATE cases SET status = '{new}' WHERE status = '{old}'"))

    op.alter_column(
        "cases",
        "status",
        server_default="intake_complete",
        existing_type=sa.String(length=50),
        existing_nullable=False,
    )

    op.add_column("cases", sa.Column("complaint_channel", sa.String(length=50), nullable=True))
    op.add_column("cases", sa.Column("police_station", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("district", sa.String(length=150), nullable=True))
    op.add_column("cases", sa.Column("unit", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("narrative_summary", sa.String(length=2000), nullable=True))
    op.add_column("cases", sa.Column("initial_txn_ref", sa.String(length=100), nullable=True))
    op.add_column("cases", sa.Column("victim_account_number", sa.String(length=100), nullable=True))
    op.add_column("cases", sa.Column("victim_ifsc", sa.String(length=50), nullable=True))
    op.add_column("cases", sa.Column("victim_bank_label", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("victim_upi_id", sa.String(length=150), nullable=True))
    op.add_column("cases", sa.Column("created_by_user_id", sa.String(length=64), nullable=True))
    op.create_index("ix_cases_initial_txn_ref", "cases", ["initial_txn_ref"])
    op.create_index("ix_cases_created_by_user_id", "cases", ["created_by_user_id"])
    op.create_foreign_key(
        "fk_cases_created_by_user_id",
        "cases",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_cases_created_by_user_id", "cases", type_="foreignkey")
    op.drop_index("ix_cases_created_by_user_id", table_name="cases")
    op.drop_index("ix_cases_initial_txn_ref", table_name="cases")
    op.drop_column("cases", "created_by_user_id")
    op.drop_column("cases", "victim_upi_id")
    op.drop_column("cases", "victim_bank_label")
    op.drop_column("cases", "victim_ifsc")
    op.drop_column("cases", "victim_account_number")
    op.drop_column("cases", "initial_txn_ref")
    op.drop_column("cases", "narrative_summary")
    op.drop_column("cases", "unit")
    op.drop_column("cases", "district")
    op.drop_column("cases", "police_station")
    op.drop_column("cases", "complaint_channel")

    reverse = {v: k for k, v in STATUS_MAP.items()}
    for new, old in reverse.items():
        op.execute(sa.text(f"UPDATE cases SET status = '{old}' WHERE status = '{new}'"))
    op.alter_column(
        "cases",
        "status",
        server_default="intake",
        existing_type=sa.String(length=50),
        existing_nullable=False,
    )
