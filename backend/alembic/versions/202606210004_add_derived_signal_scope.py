"""add derived signal scope

Revision ID: 202606210004
Revises: 202606210003
Create Date: 2026-06-21 19:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '202606210004'
down_revision: str | None = '202606210003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column(
        'derived_signal',
        sa.Column('scope', sa.Text(), server_default='overall', nullable=False),
    )
    op.create_index('ix_derived_signal_project_scope', 'derived_signal', ['project_id', 'scope'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_derived_signal_project_scope', table_name='derived_signal')
    op.drop_column('derived_signal', 'scope')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
