"""Add transaction provenance + import job graph_sync_status (Phase 7-10 audit H6/C2)."""

from alembic import op
import sqlalchemy as sa

revision = "20260718_05"
down_revision = "20260718_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("import_job_id", sa.String(length=64), nullable=True))
    op.add_column("transactions", sa.Column("source_file_name", sa.String(length=255), nullable=True))
    op.create_index("ix_transactions_import_job_id", "transactions", ["import_job_id"])
    op.create_foreign_key(
        "fk_transactions_import_job_id",
        "transactions",
        "import_jobs",
        ["import_job_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "import_jobs",
        sa.Column("graph_sync_status", sa.String(length=50), nullable=True, server_default="pending"),
    )


def downgrade() -> None:
    op.drop_column("import_jobs", "graph_sync_status")
    op.drop_constraint("fk_transactions_import_job_id", "transactions", type_="foreignkey")
    op.drop_index("ix_transactions_import_job_id", table_name="transactions")
    op.drop_column("transactions", "source_file_name")
    op.drop_column("transactions", "import_job_id")
