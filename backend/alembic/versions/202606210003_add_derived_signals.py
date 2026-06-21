"""add derived signals

Revision ID: 202606210003
Revises: 202606210002
Create Date: 2026-06-21 16:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606210003'
down_revision: str | None = '202606210002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    ('ix_derived_signal_project_type', ['project_id', 'signal_type']),
    ('ix_derived_signal_project_group', ['project_id', 'signal_group']),
    ('ix_derived_signal_project_entity', ['project_id', 'entity_type']),
    ('ix_derived_signal_project_country', ['project_id', 'country_id']),
    ('ix_derived_signal_project_company', ['project_id', 'company_id']),
    ('ix_derived_signal_project_domain', ['project_id', 'domain_id']),
    ('ix_derived_signal_project_period', ['project_id', 'date_from', 'date_to']),
    ('ix_derived_signal_project_severity', ['project_id', 'severity']),
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'derived_signal',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('signal_key', sa.Text(), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signal_type', sa.Text(), nullable=False),
        sa.Column('signal_group', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.Text(), nullable=False),
        sa.Column('entity_id', sa.Text(), nullable=True),
        sa.Column('country_id', sa.BigInteger(), nullable=True),
        sa.Column('company_id', sa.BigInteger(), nullable=True),
        sa.Column('domain_id', sa.BigInteger(), nullable=True),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('period_grain', sa.Text(), server_default='custom', nullable=False),
        sa.Column('severity', sa.Text(), nullable=False),
        sa.Column('score', sa.Numeric(10, 6), nullable=True),
        sa.Column('value', sa.Numeric(18, 6), nullable=True),
        sa.Column('baseline_value', sa.Numeric(18, 6), nullable=True),
        sa.Column('delta_value', sa.Numeric(18, 6), nullable=True),
        sa.Column('delta_percent', sa.Numeric(18, 6), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calculation_version', sa.Text(), server_default='v1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['domain_id'], ['dim_domain.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('signal_key'),
    )
    for index_name, columns in INDEXES:
        op.create_index(index_name, 'derived_signal', columns)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, _columns in reversed(INDEXES):
        op.drop_index(index_name, table_name='derived_signal')
    op.drop_table('derived_signal')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
