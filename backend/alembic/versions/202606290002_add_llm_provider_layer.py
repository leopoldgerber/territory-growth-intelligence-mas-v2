"""add llm provider layer

Revision ID: 202606290002
Revises: 202606290001
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290002'
down_revision: str | None = '202606290001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('mas_run', sa.Column('default_llm_provider', sa.Text(), nullable=True))
    op.add_column('mas_run', sa.Column('default_llm_model', sa.Text(), nullable=True))
    op.add_column('mas_run', sa.Column('prompt_version_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        'fk_mas_run_prompt_version_id_mas_prompt_version',
        'mas_run',
        'mas_prompt_version',
        ['prompt_version_id'],
        ['id'],
    )
    op.create_table(
        'mas_model_call',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('prompt_version_id', sa.BigInteger(), nullable=True),
        sa.Column('prompt_key', sa.Text(), nullable=True),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('temperature', sa.Numeric(6, 4), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('structured_output_enabled', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(18, 6), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_response_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['agent_run_id'], ['mas_agent_run.id']),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.ForeignKeyConstraint(['prompt_version_id'], ['mas_prompt_version.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_model_call_agent_run_id', 'mas_model_call', ['agent_run_id'])
    op.create_index('ix_mas_model_call_mas_run_id', 'mas_model_call', ['mas_run_id'])
    op.create_index('ix_mas_model_call_prompt_version_id', 'mas_model_call', ['prompt_version_id'])
    op.create_index('ix_mas_model_call_provider_model', 'mas_model_call', ['provider', 'model_name'])
    op.create_index('ix_mas_model_call_status', 'mas_model_call', ['status'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_mas_model_call_status', table_name='mas_model_call')
    op.drop_index('ix_mas_model_call_provider_model', table_name='mas_model_call')
    op.drop_index('ix_mas_model_call_prompt_version_id', table_name='mas_model_call')
    op.drop_index('ix_mas_model_call_mas_run_id', table_name='mas_model_call')
    op.drop_index('ix_mas_model_call_agent_run_id', table_name='mas_model_call')
    op.drop_table('mas_model_call')
    op.drop_constraint('fk_mas_run_prompt_version_id_mas_prompt_version', 'mas_run', type_='foreignkey')
    op.drop_column('mas_run', 'prompt_version_id')
    op.drop_column('mas_run', 'default_llm_model')
    op.drop_column('mas_run', 'default_llm_provider')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
