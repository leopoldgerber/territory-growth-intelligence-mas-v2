"""add mas foundation

Revision ID: 202606290001
Revises: 202606210007
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290001'
down_revision: str | None = '202606210007'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'mas_run',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column('user_query', sa.Text(), nullable=False),
        sa.Column('resolved_intent', sa.Text(), nullable=True),
        sa.Column(
            'resolved_context_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('strategy_mode', sa.Text(), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('date_from', sa.Date(), nullable=True),
        sa.Column('date_to', sa.Date(), nullable=True),
        sa.Column('budget_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('planner_output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('final_answer', sa.Text(), nullable=True),
        sa.Column('final_summary', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_run_company', 'mas_run', ['company_id'])
    op.create_index('ix_mas_run_country', 'mas_run', ['country_id'])
    op.create_index('ix_mas_run_project_created', 'mas_run', ['project_id', 'created_at'])
    op.create_index('ix_mas_run_project_status', 'mas_run', ['project_id', 'status'])
    op.create_table(
        'mas_agent_run',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.Text(), nullable=False),
        sa.Column('agent_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column(
            'input_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_agent_run_mas_run_id', 'mas_agent_run', ['mas_run_id'])
    op.create_index('ix_mas_agent_run_name', 'mas_agent_run', ['agent_name'])
    op.create_index('ix_mas_agent_run_status', 'mas_agent_run', ['status'])
    op.create_table(
        'mas_tool_call',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tool_name', sa.Text(), nullable=False),
        sa.Column('tool_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column(
            'input_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['agent_run_id'], ['mas_agent_run.id']),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_tool_call_agent_run_id', 'mas_tool_call', ['agent_run_id'])
    op.create_index('ix_mas_tool_call_mas_run_id', 'mas_tool_call', ['mas_run_id'])
    op.create_index('ix_mas_tool_call_name', 'mas_tool_call', ['tool_name'])
    op.create_index('ix_mas_tool_call_status', 'mas_tool_call', ['status'])
    op.create_table(
        'mas_evidence_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('evidence_type', sa.Text(), nullable=False),
        sa.Column('source_table', sa.Text(), nullable=True),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('context_hash', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column(
            'data_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('confidence', sa.Text(), server_default='medium', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_evidence_item_context_hash', 'mas_evidence_item', ['context_hash'])
    op.create_index('ix_mas_evidence_item_evidence_type', 'mas_evidence_item', ['evidence_type'])
    op.create_index('ix_mas_evidence_item_mas_run_id', 'mas_evidence_item', ['mas_run_id'])
    op.create_index('ix_mas_evidence_item_source_type', 'mas_evidence_item', ['source_type'])
    op.create_table(
        'mas_prompt_version',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('prompt_key', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('user_prompt_template', sa.Text(), nullable=True),
        sa.Column('output_schema_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_prompt_version_key_active', 'mas_prompt_version', ['prompt_key', 'is_active'])
    op.create_index('ix_mas_prompt_version_key_version', 'mas_prompt_version', ['prompt_key', 'version'], unique=True)
    op.create_table(
        'mas_model_provider',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('model_role', sa.Text(), nullable=False),
        sa.Column(
            'configuration_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_model_provider_provider_model', 'mas_model_provider', ['provider', 'model_name'])
    op.create_index('ix_mas_model_provider_role_active', 'mas_model_provider', ['model_role', 'is_active'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_mas_model_provider_role_active', table_name='mas_model_provider')
    op.drop_index('ix_mas_model_provider_provider_model', table_name='mas_model_provider')
    op.drop_table('mas_model_provider')
    op.drop_index('ix_mas_prompt_version_key_version', table_name='mas_prompt_version')
    op.drop_index('ix_mas_prompt_version_key_active', table_name='mas_prompt_version')
    op.drop_table('mas_prompt_version')
    op.drop_index('ix_mas_evidence_item_source_type', table_name='mas_evidence_item')
    op.drop_index('ix_mas_evidence_item_mas_run_id', table_name='mas_evidence_item')
    op.drop_index('ix_mas_evidence_item_evidence_type', table_name='mas_evidence_item')
    op.drop_index('ix_mas_evidence_item_context_hash', table_name='mas_evidence_item')
    op.drop_table('mas_evidence_item')
    op.drop_index('ix_mas_tool_call_status', table_name='mas_tool_call')
    op.drop_index('ix_mas_tool_call_name', table_name='mas_tool_call')
    op.drop_index('ix_mas_tool_call_mas_run_id', table_name='mas_tool_call')
    op.drop_index('ix_mas_tool_call_agent_run_id', table_name='mas_tool_call')
    op.drop_table('mas_tool_call')
    op.drop_index('ix_mas_agent_run_status', table_name='mas_agent_run')
    op.drop_index('ix_mas_agent_run_name', table_name='mas_agent_run')
    op.drop_index('ix_mas_agent_run_mas_run_id', table_name='mas_agent_run')
    op.drop_table('mas_agent_run')
    op.drop_index('ix_mas_run_project_status', table_name='mas_run')
    op.drop_index('ix_mas_run_project_created', table_name='mas_run')
    op.drop_index('ix_mas_run_country', table_name='mas_run')
    op.drop_index('ix_mas_run_company', table_name='mas_run')
    op.drop_table('mas_run')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
