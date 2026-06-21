"""add opportunity scores

Revision ID: 202606210005
Revises: 202606210004
Create Date: 2026-06-21 22:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606210005'
down_revision: str | None = '202606210004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    ('ix_opportunity_score_project_period', ['project_id', 'date_from', 'date_to']),
    ('ix_opportunity_score_project_scope', ['project_id', 'scope']),
    ('ix_opportunity_score_project_country', ['project_id', 'country_id']),
    ('ix_opportunity_score_project_score', ['project_id', 'opportunity_score']),
    ('ix_opportunity_score_project_category', ['project_id', 'score_category']),
    ('ix_opportunity_score_project_version', ['project_id', 'calculation_version']),
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'opportunity_score',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('country_id', sa.BigInteger(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('score_key', sa.Text(), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('opportunity_score', sa.Numeric(10, 4), nullable=False),
        sa.Column('score_category', sa.Text(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('market_size_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('growth_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('traffic_quality_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('competition_level_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('concentration_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('channel_stability_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('entry_risk_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('position_potential_score', sa.Numeric(10, 4), nullable=True),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('weaknesses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('explanation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calculation_version', sa.Text(), server_default='v1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('score_key'),
    )
    for index_name, columns in INDEXES:
        op.create_index(index_name, 'opportunity_score', columns)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, _columns in reversed(INDEXES):
        op.drop_index(index_name, table_name='opportunity_score')
    op.drop_table('opportunity_score')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
