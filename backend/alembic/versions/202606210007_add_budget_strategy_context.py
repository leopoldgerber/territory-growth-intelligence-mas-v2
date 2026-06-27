"""add budget strategy context

Revision ID: 202606210007
Revises: 202606210006
Create Date: 2026-06-21 23:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606210007'
down_revision: str | None = '202606210006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
DEPENDENCY_STATUS_DEFAULT = (
    '\'{"signals":{"required": true,"status":"existing","contexts":[]},'
    '"opportunity_score":{"required": true,"status":"existing","contexts":[]},'
    '"fallbacks_used":[]}\'::jsonb'
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('derived_signal', sa.Column('context_hash', sa.Text(), nullable=True))
    op.add_column('derived_signal', sa.Column('context_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('opportunity_score', sa.Column('context_hash', sa.Text(), nullable=True))
    op.add_column(
        'opportunity_score',
        sa.Column('context_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'budget_strategy_report',
        sa.Column('strategy_mode', sa.Text(), server_default='existing_presence', nullable=False),
    )
    op.add_column(
        'budget_strategy_report',
        sa.Column(
            'dependency_status',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(DEPENDENCY_STATUS_DEFAULT),
            nullable=False,
        ),
    )
    op.add_column(
        'budget_strategy_report',
        sa.Column('context_hash', sa.Text(), server_default='legacy', nullable=False),
    )
    op.add_column(
        'budget_strategy_report',
        sa.Column(
            'context_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
    )
    op.create_index('ix_budget_strategy_project_mode', 'budget_strategy_report', ['project_id', 'strategy_mode'])
    op.create_index('ix_budget_strategy_context_hash', 'budget_strategy_report', ['context_hash'])
    op.create_index('ix_derived_signal_context_hash', 'derived_signal', ['context_hash'])
    op.create_index('ix_opportunity_score_context_hash', 'opportunity_score', ['context_hash'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_opportunity_score_context_hash', table_name='opportunity_score')
    op.drop_index('ix_derived_signal_context_hash', table_name='derived_signal')
    op.drop_index('ix_budget_strategy_context_hash', table_name='budget_strategy_report')
    op.drop_index('ix_budget_strategy_project_mode', table_name='budget_strategy_report')
    op.drop_column('budget_strategy_report', 'context_json')
    op.drop_column('budget_strategy_report', 'context_hash')
    op.drop_column('budget_strategy_report', 'dependency_status')
    op.drop_column('budget_strategy_report', 'strategy_mode')
    op.drop_column('opportunity_score', 'context_json')
    op.drop_column('opportunity_score', 'context_hash')
    op.drop_column('derived_signal', 'context_json')
    op.drop_column('derived_signal', 'context_hash')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
