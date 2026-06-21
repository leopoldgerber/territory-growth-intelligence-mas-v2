"""add budget strategy reports

Revision ID: 202606210006
Revises: 202606210005
Create Date: 2026-06-21 23:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606210006'
down_revision: str | None = '202606210005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'budget_strategy_report',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('country_id', sa.BigInteger(), nullable=False),
        sa.Column('strategy_key', sa.Text(), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('budget_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), server_default='generated', nullable=False),
        sa.Column('opportunity_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('opportunity_score_id', sa.BigInteger(), nullable=True),
        sa.Column('recommended_approach', sa.Text(), nullable=False),
        sa.Column('allocation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('channel_roles', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expected_effect', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('risks', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('explanation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('calculation_version', sa.Text(), server_default='v1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['opportunity_score_id'], ['opportunity_score.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_key'),
    )
    op.create_index(
        'ix_budget_strategy_project_period',
        'budget_strategy_report',
        ['project_id', 'date_from', 'date_to'],
    )
    op.create_index('ix_budget_strategy_project_country', 'budget_strategy_report', ['project_id', 'country_id'])
    op.create_index('ix_budget_strategy_project_scope', 'budget_strategy_report', ['project_id', 'scope'])
    op.create_index('ix_budget_strategy_project_created', 'budget_strategy_report', ['project_id', 'created_at'])
    op.create_index(
        'ix_budget_strategy_project_version',
        'budget_strategy_report',
        ['project_id', 'calculation_version'],
    )
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name in (
        'ix_budget_strategy_project_version', 'ix_budget_strategy_project_created',
        'ix_budget_strategy_project_scope', 'ix_budget_strategy_project_country',
        'ix_budget_strategy_project_period',
    ):
        op.drop_index(index_name, table_name='budget_strategy_report')
    op.drop_table('budget_strategy_report')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
