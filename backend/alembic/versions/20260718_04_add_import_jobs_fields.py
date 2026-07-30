"""Add Phase 7 ingestion tracking fields to import_jobs.

Revision ID: 20260718_04
Revises: 20260718_03
Create Date: 2026-07-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260718_04"
down_revision: Union[str, None] = "20260718_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("import_jobs", sa.Column("rejected_records", sa.Integer(), server_default="0", nullable=False))
    op.add_column("import_jobs", sa.Column("content_hash", sa.String(length=128), nullable=True))
    op.add_column("import_jobs", sa.Column("error_report_json", sa.Text(), nullable=True))
    op.create_index(op.f("ix_import_jobs_content_hash"), "import_jobs", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_import_jobs_content_hash"), table_name="import_jobs")
    op.drop_column("import_jobs", "error_report_json")
    op.drop_column("import_jobs", "content_hash")
    op.drop_column("import_jobs", "rejected_records")
