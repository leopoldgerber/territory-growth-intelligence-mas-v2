"""add alerts layer

Revision ID: 202606290007
Revises: 202606290006
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290007'
down_revision: str | None = '202606290006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'data_update_batch',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_file', sa.Text(), nullable=True),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('rows_loaded', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('rows_failed', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('validation_status', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_data_update_batch_project_created', 'data_update_batch', ['project_id', 'created_at'])
    op.create_index('ix_data_update_batch_project_source', 'data_update_batch', ['project_id', 'source_type'])
    op.create_index('ix_data_update_batch_status', 'data_update_batch', ['status'])
    op.create_table(
        'data_freshness_status',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_type', sa.Text(), nullable=False),
        sa.Column('latest_available_date', sa.Date(), nullable=True),
        sa.Column('latest_loaded_date', sa.Date(), nullable=True),
        sa.Column('last_update_batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('freshness_status', sa.Text(), nullable=False, server_default='unknown'),
        sa.Column('lag_days', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['last_update_batch_id'], ['data_update_batch.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_data_freshness_project_dataset',
        'data_freshness_status',
        ['project_id', 'dataset_type'],
        unique=True,
    )
    op.create_index('ix_data_freshness_status', 'data_freshness_status', ['freshness_status'])
    op.create_table(
        'analytics_recalculation_job',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data_update_batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('calculation_version', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metrics_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['data_update_batch_id'], ['data_update_batch.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_analytics_recalculation_batch', 'analytics_recalculation_job', ['data_update_batch_id'])
    op.create_index(
        'ix_analytics_recalculation_project_created',
        'analytics_recalculation_job',
        ['project_id', 'started_at'],
    )
    op.create_index('ix_analytics_recalculation_type_status', 'analytics_recalculation_job', ['job_type', 'status'])
    op.create_table(
        'alert_rule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity_default', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('threshold_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('cooldown_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('scope_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alert_rule_enabled', 'alert_rule', ['is_enabled'])
    op.create_index('ix_alert_rule_project_type', 'alert_rule', ['project_id', 'alert_type'])
    op.create_table(
        'alert_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_rule_id', sa.BigInteger(), nullable=True),
        sa.Column('alert_type', sa.Text(), nullable=False),
        sa.Column('severity', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='new'),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('competitor_id', sa.BigInteger(), nullable=True),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('details_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('evidence_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('related_signal_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('related_score_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('related_insight_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('context_hash', sa.Text(), nullable=True),
        sa.Column('dedupe_key', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rule.id']),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['competitor_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alert_event_context_hash', 'alert_event', ['context_hash'])
    op.create_index('ix_alert_event_dedupe_key', 'alert_event', ['dedupe_key'])
    op.create_index('ix_alert_event_project_created', 'alert_event', ['project_id', 'created_at'])
    op.create_index('ix_alert_event_project_severity', 'alert_event', ['project_id', 'severity'])
    op.create_index('ix_alert_event_project_status', 'alert_event', ['project_id', 'status'])
    op.create_index('ix_alert_event_project_type', 'alert_event', ['project_id', 'alert_type'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_alert_event_project_type', table_name='alert_event')
    op.drop_index('ix_alert_event_project_status', table_name='alert_event')
    op.drop_index('ix_alert_event_project_severity', table_name='alert_event')
    op.drop_index('ix_alert_event_project_created', table_name='alert_event')
    op.drop_index('ix_alert_event_dedupe_key', table_name='alert_event')
    op.drop_index('ix_alert_event_context_hash', table_name='alert_event')
    op.drop_table('alert_event')
    op.drop_index('ix_alert_rule_project_type', table_name='alert_rule')
    op.drop_index('ix_alert_rule_enabled', table_name='alert_rule')
    op.drop_table('alert_rule')
    op.drop_index('ix_analytics_recalculation_type_status', table_name='analytics_recalculation_job')
    op.drop_index('ix_analytics_recalculation_project_created', table_name='analytics_recalculation_job')
    op.drop_index('ix_analytics_recalculation_batch', table_name='analytics_recalculation_job')
    op.drop_table('analytics_recalculation_job')
    op.drop_index('ix_data_freshness_status', table_name='data_freshness_status')
    op.drop_index('ix_data_freshness_project_dataset', table_name='data_freshness_status')
    op.drop_table('data_freshness_status')
    op.drop_index('ix_data_update_batch_status', table_name='data_update_batch')
    op.drop_index('ix_data_update_batch_project_source', table_name='data_update_batch')
    op.drop_index('ix_data_update_batch_project_created', table_name='data_update_batch')
    op.drop_table('data_update_batch')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
