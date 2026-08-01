"""CD-1: call_tickets, call_ticket_proofs, case intake_source / call_ticket_id."""

from alembic import op
import sqlalchemy as sa

revision = "20260801_01"
down_revision = "20260718_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "call_tickets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("ticket_number", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("ani_phone", sa.String(length=50), nullable=True),
        sa.Column("operator_user_id", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("elapsed_to_case_seconds", sa.Integer(), nullable=True),
        sa.Column("fraud_category", sa.String(length=50), nullable=True),
        sa.Column("amount_at_risk", sa.Float(), nullable=True),
        sa.Column("complainant_name", sa.String(length=255), nullable=True),
        sa.Column("complainant_phone", sa.String(length=50), nullable=True),
        sa.Column("txn_relative_time", sa.String(length=50), nullable=True),
        sa.Column("layer1_upi", sa.String(length=150), nullable=True),
        sa.Column("layer1_account", sa.String(length=100), nullable=True),
        sa.Column("layer1_ifsc", sa.String(length=50), nullable=True),
        sa.Column("layer1_bank", sa.String(length=255), nullable=True),
        sa.Column("utr", sa.String(length=100), nullable=True),
        sa.Column("narrative_short", sa.String(length=1000), nullable=True),
        sa.Column("ncrp_acknowledgement_number", sa.String(length=100), nullable=True),
        sa.Column("case_id", sa.String(length=64), nullable=True),
        sa.Column("proof_token", sa.String(length=64), nullable=True),
        sa.Column("proof_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_channel", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["operator_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_number"),
        sa.UniqueConstraint("proof_token"),
    )
    op.create_index("ix_call_tickets_ticket_number", "call_tickets", ["ticket_number"])
    op.create_index("ix_call_tickets_status", "call_tickets", ["status"])
    op.create_index("ix_call_tickets_ani_phone", "call_tickets", ["ani_phone"])
    op.create_index("ix_call_tickets_operator_user_id", "call_tickets", ["operator_user_id"])
    op.create_index("ix_call_tickets_case_id", "call_tickets", ["case_id"])
    op.create_index("ix_call_tickets_proof_token", "call_tickets", ["proof_token"])

    op.create_table(
        "call_ticket_proofs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("ticket_id", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_via", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["call_tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_call_ticket_proofs_ticket_id", "call_ticket_proofs", ["ticket_id"])
    op.create_index("ix_call_ticket_proofs_sha256_hash", "call_ticket_proofs", ["sha256_hash"])

    op.add_column("cases", sa.Column("intake_source", sa.String(length=40), nullable=True))
    op.add_column("cases", sa.Column("call_ticket_id", sa.String(length=64), nullable=True))
    op.create_index("ix_cases_intake_source", "cases", ["intake_source"])
    op.create_index("ix_cases_call_ticket_id", "cases", ["call_ticket_id"])
    op.create_foreign_key(
        "fk_cases_call_ticket_id",
        "cases",
        "call_tickets",
        ["call_ticket_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_cases_call_ticket_id", "cases", type_="foreignkey")
    op.drop_index("ix_cases_call_ticket_id", table_name="cases")
    op.drop_index("ix_cases_intake_source", table_name="cases")
    op.drop_column("cases", "call_ticket_id")
    op.drop_column("cases", "intake_source")

    op.drop_index("ix_call_ticket_proofs_sha256_hash", table_name="call_ticket_proofs")
    op.drop_index("ix_call_ticket_proofs_ticket_id", table_name="call_ticket_proofs")
    op.drop_table("call_ticket_proofs")

    op.drop_index("ix_call_tickets_proof_token", table_name="call_tickets")
    op.drop_index("ix_call_tickets_case_id", table_name="call_tickets")
    op.drop_index("ix_call_tickets_operator_user_id", table_name="call_tickets")
    op.drop_index("ix_call_tickets_ani_phone", table_name="call_tickets")
    op.drop_index("ix_call_tickets_status", table_name="call_tickets")
    op.drop_index("ix_call_tickets_ticket_number", table_name="call_tickets")
    op.drop_table("call_tickets")
