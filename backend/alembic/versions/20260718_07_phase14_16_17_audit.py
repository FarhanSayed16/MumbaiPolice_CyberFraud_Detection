"""Phase 14-17 audit: cluster links, case sla_breached (H8-H9, H19)."""

from alembic import op
import sqlalchemy as sa

revision = "20260718_07"
down_revision = "20260718_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("network_clusters", sa.Column("run_id", sa.String(length=64), nullable=True))
    op.add_column("network_clusters", sa.Column("linked_case_ids", sa.JSON(), nullable=True))
    op.add_column("network_clusters", sa.Column("linked_account_ids", sa.JSON(), nullable=True))
    op.add_column("network_clusters", sa.Column("next_account_id", sa.String(length=64), nullable=True))
    op.add_column(
        "network_clusters",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_network_clusters_run_id", "network_clusters", ["run_id"])
    op.create_index("ix_network_clusters_is_active", "network_clusters", ["is_active"])

    op.add_column(
        "cases",
        sa.Column("sla_breached", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_cases_sla_breached", "cases", ["sla_breached"])


def downgrade() -> None:
    op.drop_index("ix_cases_sla_breached", table_name="cases")
    op.drop_column("cases", "sla_breached")

    op.drop_index("ix_network_clusters_is_active", table_name="network_clusters")
    op.drop_index("ix_network_clusters_run_id", table_name="network_clusters")
    op.drop_column("network_clusters", "is_active")
    op.drop_column("network_clusters", "next_account_id")
    op.drop_column("network_clusters", "linked_account_ids")
    op.drop_column("network_clusters", "linked_case_ids")
    op.drop_column("network_clusters", "run_id")
