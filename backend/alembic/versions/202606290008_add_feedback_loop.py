"""add feedback loop

Revision ID: 202606290008
Revises: 202606290007
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290008'
down_revision: str | None = '202606290007'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('recommendation', sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('recommendation', sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('recommendation', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('recommendation', sa.Column('owner', sa.Text(), nullable=True))
    op.add_column(
        'recommendation',
        sa.Column('expected_outcome_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'recommendation',
        sa.Column('actual_outcome_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'recommendation',
        sa.Column('feedback_status', sa.Text(), nullable=False, server_default='not_reviewed'),
    )
    op.add_column('recommendation', sa.Column('linked_campaign_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        'recommendation',
        sa.Column('learning_status', sa.Text(), nullable=False, server_default='not_started'),
    )
    op.create_table(
        'recommendation_decision',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('reason_category', sa.Text(), nullable=False, server_default='unknown'),
        sa.Column('reason_text', sa.Text(), nullable=True),
        sa.Column('expected_action_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recommendation_decision_created', 'recommendation_decision', ['project_id', 'created_at'])
    op.create_index('ix_recommendation_decision_decision', 'recommendation_decision', ['decision'])
    op.create_index('ix_recommendation_decision_recommendation', 'recommendation_decision', ['recommendation_id'])
    op.create_table(
        'action_execution',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('strategy_mode', sa.Text(), nullable=True),
        sa.Column('action_type', sa.Text(), nullable=False),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('planned_budget', sa.Numeric(18, 2), nullable=True),
        sa.Column('actual_budget', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='planned'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_action_execution_created', 'action_execution', ['project_id', 'created_at'])
    op.create_index('ix_action_execution_recommendation', 'action_execution', ['recommendation_id'])
    op.create_index('ix_action_execution_status', 'action_execution', ['status'])
    op.create_table(
        'action_result',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('period_from', sa.Date(), nullable=True),
        sa.Column('period_to', sa.Date(), nullable=True),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('traffic', sa.BigInteger(), nullable=True),
        sa.Column('traffic_growth', sa.Numeric(12, 6), nullable=True),
        sa.Column('bounce_rate', sa.Numeric(10, 6), nullable=True),
        sa.Column('avg_visit_duration', sa.Numeric(12, 4), nullable=True),
        sa.Column('pages_per_visit', sa.Numeric(10, 4), nullable=True),
        sa.Column('spend', sa.Numeric(18, 2), nullable=True),
        sa.Column('conversions', sa.Numeric(18, 4), nullable=True),
        sa.Column('revenue', sa.Numeric(18, 2), nullable=True),
        sa.Column('cac', sa.Numeric(18, 4), nullable=True),
        sa.Column('cpa', sa.Numeric(18, 4), nullable=True),
        sa.Column('roi', sa.Numeric(18, 6), nullable=True),
        sa.Column('payback_days', sa.Integer(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['action_execution_id'], ['action_execution.id']),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_action_result_action', 'action_result', ['action_execution_id'])
    op.create_index('ix_action_result_created', 'action_result', ['project_id', 'created_at'])
    op.create_index('ix_action_result_recommendation', 'action_result', ['recommendation_id'])
    op.create_table(
        'recommendation_expectation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expected_direction', sa.Text(), nullable=False),
        sa.Column('expected_metric', sa.Text(), nullable=False),
        sa.Column('expected_value_min', sa.Numeric(18, 6), nullable=True),
        sa.Column('expected_value_max', sa.Numeric(18, 6), nullable=True),
        sa.Column('expected_time_window_days', sa.Integer(), nullable=True),
        sa.Column('assumptions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('confidence', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recommendation_expectation_created', 'recommendation_expectation', ['project_id', 'created_at'])
    op.create_index('ix_recommendation_expectation_metric', 'recommendation_expectation', ['expected_metric'])
    op.create_index('ix_recommendation_expectation_recommendation', 'recommendation_expectation', ['recommendation_id'])
    op.create_table(
        'assumption',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assumption_type', sa.Text(), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('evidence_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_assumption_created', 'assumption', ['project_id', 'created_at'])
    op.create_index('ix_assumption_recommendation', 'assumption', ['recommendation_id'])
    op.create_index('ix_assumption_status', 'assumption', ['status'])
    op.create_table(
        'learning_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('learning_type', sa.Text(), nullable=False),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('details_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('impact_area', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['action_execution_id'], ['action_execution.id']),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_learning_event_created', 'learning_event', ['project_id', 'created_at'])
    op.create_index('ix_learning_event_recommendation', 'learning_event', ['recommendation_id'])
    op.create_index('ix_learning_event_status', 'learning_event', ['status'])
    op.create_index('ix_learning_event_type', 'learning_event', ['learning_type'])
    op.create_table(
        'scoring_model_review',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_learning_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('current_version', sa.Text(), nullable=False),
        sa.Column('proposed_version', sa.Text(), nullable=True),
        sa.Column(
            'proposed_changes_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{}',
        ),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='proposed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_learning_event_id'], ['learning_event.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scoring_model_review_created', 'scoring_model_review', ['project_id', 'created_at'])
    op.create_index('ix_scoring_model_review_learning', 'scoring_model_review', ['source_learning_event_id'])
    op.create_index('ix_scoring_model_review_status', 'scoring_model_review', ['status'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_scoring_model_review_status', table_name='scoring_model_review')
    op.drop_index('ix_scoring_model_review_learning', table_name='scoring_model_review')
    op.drop_index('ix_scoring_model_review_created', table_name='scoring_model_review')
    op.drop_table('scoring_model_review')
    op.drop_index('ix_learning_event_type', table_name='learning_event')
    op.drop_index('ix_learning_event_status', table_name='learning_event')
    op.drop_index('ix_learning_event_recommendation', table_name='learning_event')
    op.drop_index('ix_learning_event_created', table_name='learning_event')
    op.drop_table('learning_event')
    op.drop_index('ix_assumption_status', table_name='assumption')
    op.drop_index('ix_assumption_recommendation', table_name='assumption')
    op.drop_index('ix_assumption_created', table_name='assumption')
    op.drop_table('assumption')
    op.drop_index('ix_recommendation_expectation_recommendation', table_name='recommendation_expectation')
    op.drop_index('ix_recommendation_expectation_metric', table_name='recommendation_expectation')
    op.drop_index('ix_recommendation_expectation_created', table_name='recommendation_expectation')
    op.drop_table('recommendation_expectation')
    op.drop_index('ix_action_result_recommendation', table_name='action_result')
    op.drop_index('ix_action_result_created', table_name='action_result')
    op.drop_index('ix_action_result_action', table_name='action_result')
    op.drop_table('action_result')
    op.drop_index('ix_action_execution_status', table_name='action_execution')
    op.drop_index('ix_action_execution_recommendation', table_name='action_execution')
    op.drop_index('ix_action_execution_created', table_name='action_execution')
    op.drop_table('action_execution')
    op.drop_index('ix_recommendation_decision_recommendation', table_name='recommendation_decision')
    op.drop_index('ix_recommendation_decision_decision', table_name='recommendation_decision')
    op.drop_index('ix_recommendation_decision_created', table_name='recommendation_decision')
    op.drop_table('recommendation_decision')
    op.drop_column('recommendation', 'learning_status')
    op.drop_column('recommendation', 'linked_campaign_id')
    op.drop_column('recommendation', 'feedback_status')
    op.drop_column('recommendation', 'actual_outcome_json')
    op.drop_column('recommendation', 'expected_outcome_json')
    op.drop_column('recommendation', 'owner')
    op.drop_column('recommendation', 'completed_at')
    op.drop_column('recommendation', 'rejected_at')
    op.drop_column('recommendation', 'accepted_at')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
