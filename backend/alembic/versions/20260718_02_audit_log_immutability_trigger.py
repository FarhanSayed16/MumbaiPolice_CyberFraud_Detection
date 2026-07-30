"""audit log immutability trigger (`Sub-phase 4.3`)

Revision ID: 20260718_02
Revises: 20260718_01
Create Date: 2026-07-18 01:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260718_02'
down_revision: Union[str, None] = '20260718_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create evidentiary-grade PostgreSQL trigger blocking any UPDATE or DELETE operation on audit_logs.
    Even if an application vulnerability attempts SQL query execution against audit_logs, the database engine rejects it.
    """
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_audit_update_delete()
    RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'Evidentiary Grade Protection: audit_logs table is append-only. UPDATE and DELETE operations are strictly prohibited under BNSS & IT Act compliance.';
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_modify ON audit_logs;")
    op.execute("""
    CREATE TRIGGER trg_prevent_audit_modify
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_update_delete();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_modify ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_update_delete();")
