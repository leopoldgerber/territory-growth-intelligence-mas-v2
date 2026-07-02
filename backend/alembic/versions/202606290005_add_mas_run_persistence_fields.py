"""add mas run persistence fields

Revision ID: 202606290005
Revises: 202606290004
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290005'
down_revision: str | None = '202606290004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('mas_run', sa.Column('synthesis_output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('mas_run', sa.Column('metrics_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_column('mas_run', 'metrics_json')
    op.drop_column('mas_run', 'synthesis_output_json')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
