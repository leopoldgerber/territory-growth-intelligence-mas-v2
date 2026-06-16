"""add fact calendar fields

Revision ID: 202605310001
Revises: 202605240002
Create Date: 2026-05-31 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '202605310001'
down_revision: str | None = '202605240002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


FACT_TABLES = (
    'fact_traffic_countries_daily',
    'fact_traffic_sources_daily',
    'fact_journey_sources_daily',
    'fact_device_trends_daily',
)


def calendar_columns() -> list[sa.Column]:
    """Build calendar column definitions.
    Args:
        None (None): No arguments are required."""
    columns = [
        sa.Column('day', sa.Integer(), nullable=True),
        sa.Column('day_of_week', sa.Text(), nullable=True),
        sa.Column('week_of_year', sa.Integer(), nullable=True),
        sa.Column('is_weekend', sa.Boolean(), nullable=True),
        sa.Column('month', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('month_number', sa.Integer(), nullable=True),
        sa.Column('month_year', sa.Date(), nullable=True),
    ]
    return columns


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    for table_name in FACT_TABLES:
        for column in calendar_columns():
            op.add_column(table_name, column.copy())
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    column_names = [column.name for column in calendar_columns()]
    for table_name in FACT_TABLES:
        for column_name in reversed(column_names):
            op.drop_column(table_name, column_name)
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
