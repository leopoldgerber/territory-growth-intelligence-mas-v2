"""add history layer

Revision ID: 202606290006
Revises: 202606290005
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290006'
down_revision: str | None = '202606290005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'report_snapshot',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('context_hash', sa.Text(), nullable=True),
        sa.Column('strategy_mode', sa.Text(), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('company_domain', sa.Text(), nullable=True),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('budget_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('calculation_version', sa.Text(), nullable=True),
        sa.Column('scoring_version', sa.Text(), nullable=True),
        sa.Column('prompt_version_id', sa.BigInteger(), nullable=True),
        sa.Column('llm_provider', sa.Text(), nullable=True),
        sa.Column('llm_model', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('report_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('markdown_snapshot', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['prompt_version_id'], ['mas_prompt_version.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_report_snapshot_context_hash', 'report_snapshot', ['context_hash'])
    op.create_index('ix_report_snapshot_mas_run_id', 'report_snapshot', ['mas_run_id'])
    op.create_index('ix_report_snapshot_project_created', 'report_snapshot', ['project_id', 'created_at'])
    op.create_index('ix_report_snapshot_project_type', 'report_snapshot', ['project_id', 'report_type'])
    op.create_index('ix_report_snapshot_status', 'report_snapshot', ['status'])
    op.create_table(
        'insight',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('report_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evidence_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('insight_type', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('severity', sa.Text(), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('strategy_mode', sa.Text(), nullable=True),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('details_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['evidence_item_id'], ['mas_evidence_item.id']),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['report_snapshot_id'], ['report_snapshot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_insight_mas_run_id', 'insight', ['mas_run_id'])
    op.create_index('ix_insight_project_created', 'insight', ['project_id', 'created_at'])
    op.create_index('ix_insight_project_type', 'insight', ['project_id', 'insight_type'])
    op.create_index('ix_insight_report_snapshot_id', 'insight', ['report_snapshot_id'])
    op.create_index('ix_insight_status', 'insight', ['status'])
    op.create_table(
        'recommendation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('report_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('insight_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommendation_type', sa.Text(), nullable=False),
        sa.Column('strategy_mode', sa.Text(), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('priority', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('budget_share', sa.Numeric(10, 4), nullable=True),
        sa.Column('budget_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('status', sa.Text(), nullable=False, server_default='proposed'),
        sa.Column('user_decision', sa.Text(), nullable=True),
        sa.Column('user_decision_reason', sa.Text(), nullable=True),
        sa.Column('linked_mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('linked_evidence_item_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['insight_id'], ['insight.id']),
        sa.ForeignKeyConstraint(['linked_mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['report_snapshot_id'], ['report_snapshot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recommendation_mas_run_id', 'recommendation', ['mas_run_id'])
    op.create_index('ix_recommendation_project_created', 'recommendation', ['project_id', 'created_at'])
    op.create_index('ix_recommendation_project_type', 'recommendation', ['project_id', 'recommendation_type'])
    op.create_index('ix_recommendation_report_snapshot_id', 'recommendation', ['report_snapshot_id'])
    op.create_index('ix_recommendation_status', 'recommendation', ['status'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_recommendation_status', table_name='recommendation')
    op.drop_index('ix_recommendation_report_snapshot_id', table_name='recommendation')
    op.drop_index('ix_recommendation_project_type', table_name='recommendation')
    op.drop_index('ix_recommendation_project_created', table_name='recommendation')
    op.drop_index('ix_recommendation_mas_run_id', table_name='recommendation')
    op.drop_table('recommendation')
    op.drop_index('ix_insight_status', table_name='insight')
    op.drop_index('ix_insight_report_snapshot_id', table_name='insight')
    op.drop_index('ix_insight_project_type', table_name='insight')
    op.drop_index('ix_insight_project_created', table_name='insight')
    op.drop_index('ix_insight_mas_run_id', table_name='insight')
    op.drop_table('insight')
    op.drop_index('ix_report_snapshot_status', table_name='report_snapshot')
    op.drop_index('ix_report_snapshot_project_type', table_name='report_snapshot')
    op.drop_index('ix_report_snapshot_project_created', table_name='report_snapshot')
    op.drop_index('ix_report_snapshot_mas_run_id', table_name='report_snapshot')
    op.drop_index('ix_report_snapshot_context_hash', table_name='report_snapshot')
    op.drop_table('report_snapshot')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
