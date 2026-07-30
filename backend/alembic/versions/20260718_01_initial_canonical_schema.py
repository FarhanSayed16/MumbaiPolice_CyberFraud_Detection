"""initial canonical schema (`Sub-phase 3.1` & `3.2`)

Revision ID: 20260718_01
Revises: 
Create Date: 2026-07-18 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260718_01'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='officer'),
        sa.Column('badge_number', sa.String(100), nullable=True),
        sa.Column('police_station_unit', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # 2. Accounts Table
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('stable_id', sa.String(128), nullable=False),
        sa.Column('account_number', sa.String(100), nullable=True),
        sa.Column('ifsc_code', sa.String(50), nullable=True),
        sa.Column('bank_name', sa.String(255), nullable=True),
        sa.Column('upi_id', sa.String(150), nullable=True),
        sa.Column('wallet_id', sa.String(150), nullable=True),
        sa.Column('account_holder_name', sa.String(255), nullable=True),
        sa.Column('account_type', sa.String(50), nullable=True),
        sa.Column('freeze_status', sa.String(50), nullable=False, server_default='unfrozen'),
        sa.Column('cash_out_detected', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('layer_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_accounts_stable_id', 'accounts', ['stable_id'], unique=True)
    op.create_index('ix_accounts_account_number', 'accounts', ['account_number'])
    op.create_index('ix_accounts_ifsc_code', 'accounts', ['ifsc_code'])
    op.create_index('ix_accounts_upi_id', 'accounts', ['upi_id'])
    op.create_index('ix_accounts_freeze_status', 'accounts', ['freeze_status'])
    op.create_index('ix_accounts_layer_number', 'accounts', ['layer_number'])
    op.create_index('ix_accounts_deleted_at', 'accounts', ['deleted_at'])

    # 3. Cases Table
    op.create_table(
        'cases',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('case_number', sa.String(100), nullable=False),
        sa.Column('fir_number', sa.String(100), nullable=True),
        sa.Column('ncrp_acknowledgement_number', sa.String(100), nullable=True),
        sa.Column('fraud_category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='intake'),
        sa.Column('amount_at_risk', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('amount_frozen', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('complainant_name', sa.String(255), nullable=True),
        sa.Column('complainant_phone', sa.String(50), nullable=True),
        sa.Column('complainant_email', sa.String(255), nullable=True),
        sa.Column('assigned_to_user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('sla_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspicion_flags_json', sa.JSON(), nullable=True),
        sa.Column('duplicate_of_case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_cases_case_number', 'cases', ['case_number'], unique=True)
    op.create_index('ix_cases_fir_number', 'cases', ['fir_number'])
    op.create_index('ix_cases_ncrp_acknowledgement_number', 'cases', ['ncrp_acknowledgement_number'])
    op.create_index('ix_cases_fraud_category', 'cases', ['fraud_category'])
    op.create_index('ix_cases_status', 'cases', ['status'])
    op.create_index('ix_cases_complainant_phone', 'cases', ['complainant_phone'])
    op.create_index('ix_cases_assigned_to_user_id', 'cases', ['assigned_to_user_id'])
    op.create_index('ix_cases_sla_due_at', 'cases', ['sla_due_at'])
    op.create_index('ix_cases_duplicate_of_case_id', 'cases', ['duplicate_of_case_id'])
    op.create_index('ix_cases_deleted_at', 'cases', ['deleted_at'])

    # 4. CaseAccounts Association Table
    op.create_table(
        'case_accounts',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', sa.String(64), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_in_case', sa.String(50), nullable=False, server_default='suspect_layer1'),
        sa.Column('amount_transferred', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('freeze_requested', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('freeze_confirmed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_case_accounts_case_id', 'case_accounts', ['case_id'])
    op.create_index('ix_case_accounts_account_id', 'case_accounts', ['account_id'])
    op.create_index('ix_case_accounts_role_in_case', 'case_accounts', ['role_in_case'])

    # 5. Transactions Table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_account_id', sa.String(64), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_account_id', sa.String(64), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('utr_number', sa.String(100), nullable=True),
        sa.Column('rrn_number', sa.String(100), nullable=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False, server_default='IMPS'),
        sa.Column('withdrawal_flag', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('raw_narration', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_transactions_case_id', 'transactions', ['case_id'])
    op.create_index('ix_transactions_source_account_id', 'transactions', ['source_account_id'])
    op.create_index('ix_transactions_target_account_id', 'transactions', ['target_account_id'])
    op.create_index('ix_transactions_utr_number', 'transactions', ['utr_number'])
    op.create_index('ix_transactions_rrn_number', 'transactions', ['rrn_number'])
    op.create_index('ix_transactions_transaction_date', 'transactions', ['transaction_date'])
    op.create_index('ix_transactions_transaction_type', 'transactions', ['transaction_type'])
    op.create_index('ix_transactions_withdrawal_flag', 'transactions', ['withdrawal_flag'])
    op.create_index('ix_transactions_deleted_at', 'transactions', ['deleted_at'])

    # 6. Notices Table
    op.create_table(
        'notices',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('notice_number', sa.String(100), nullable=False),
        sa.Column('case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_account_id', sa.String(64), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notice_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='drafted'),
        sa.Column('recipient_bank_name', sa.String(255), nullable=True),
        sa.Column('recipient_nodal_email', sa.String(255), nullable=True),
        sa.Column('recipient_bank_ifsc', sa.String(50), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sla_deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_summary', sa.Text(), nullable=True),
        sa.Column('pdf_file_path', sa.String(500), nullable=True),
        sa.Column('supersedes_notice_id', sa.String(64), sa.ForeignKey('notices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('issued_by_user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_notices_notice_number', 'notices', ['notice_number'], unique=True)
    op.create_index('ix_notices_case_id', 'notices', ['case_id'])
    op.create_index('ix_notices_target_account_id', 'notices', ['target_account_id'])
    op.create_index('ix_notices_notice_type', 'notices', ['notice_type'])
    op.create_index('ix_notices_status', 'notices', ['status'])
    op.create_index('ix_notices_sla_deadline_at', 'notices', ['sla_deadline_at'])
    op.create_index('ix_notices_supersedes_notice_id', 'notices', ['supersedes_notice_id'])
    op.create_index('ix_notices_deleted_at', 'notices', ['deleted_at'])

    # 7. Evidences Table
    op.create_table(
        'evidences',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('uploaded_by_user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_evidences_case_id', 'evidences', ['case_id'])
    op.create_index('ix_evidences_sha256_hash', 'evidences', ['sha256_hash'])
    op.create_index('ix_evidences_deleted_at', 'evidences', ['deleted_at'])

    # 8. AuditLogs Table (Immutable)
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_user_email', 'audit_logs', ['user_email'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # 9. Notifications Table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=True),
        sa.Column('notice_id', sa.String(64), sa.ForeignKey('notices.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])

    # 10. WatchlistEntries Table
    op.create_table(
        'watchlist_entries',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('account_number', sa.String(100), nullable=True),
        sa.Column('ifsc_code', sa.String(50), nullable=True),
        sa.Column('upi_id', sa.String(150), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='85.0'),
        sa.Column('added_by_user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_watchlist_entries_account_number', 'watchlist_entries', ['account_number'])
    op.create_index('ix_watchlist_entries_ifsc_code', 'watchlist_entries', ['ifsc_code'])
    op.create_index('ix_watchlist_entries_upi_id', 'watchlist_entries', ['upi_id'])
    op.create_index('ix_watchlist_entries_risk_score', 'watchlist_entries', ['risk_score'])
    op.create_index('ix_watchlist_entries_is_active', 'watchlist_entries', ['is_active'])

    # 11. ImportJobs Table
    op.create_table(
        'import_jobs',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('case_id', sa.String(64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=True),
        sa.Column('uploaded_by_user_id', sa.String(64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_import_jobs_case_id', 'import_jobs', ['case_id'])
    op.create_index('ix_import_jobs_status', 'import_jobs', ['status'])

    # 12. NetworkClusters Table
    op.create_table(
        'network_clusters',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('cluster_name', sa.String(255), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='90.0'),
        sa.Column('total_cases_involved', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_accounts_involved', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_amount_involved', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('graph_summary_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_network_clusters_cluster_name', 'network_clusters', ['cluster_name'])
    op.create_index('ix_network_clusters_risk_score', 'network_clusters', ['risk_score'])

    # 13. Templates Table
    op.create_table(
        'templates',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('notice_type', sa.String(50), nullable=False),
        sa.Column('subject_template', sa.String(500), nullable=False),
        sa.Column('body_template_jinja', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_templates_template_name', 'templates', ['template_name'], unique=True)
    op.create_index('ix_templates_notice_type', 'templates', ['notice_type'])
    op.create_index('ix_templates_is_active', 'templates', ['is_active'])


def downgrade() -> None:
    op.drop_table('templates')
    op.drop_table('network_clusters')
    op.drop_table('import_jobs')
    op.drop_table('watchlist_entries')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('evidences')
    op.drop_table('notices')
    op.drop_table('transactions')
    op.drop_table('case_accounts')
    op.drop_table('cases')
    op.drop_table('accounts')
    op.drop_table('users')
