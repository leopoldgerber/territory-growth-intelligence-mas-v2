"""add competitor intelligence indexes

Revision ID: 202606190001
Revises: 202606170002
Create Date: 2026-06-19 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '202606190001'
down_revision: str | None = '202606170002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    (
        'ix_fact_traffic_countries_project_company_country_date',
        ['project_id', 'company_id', 'country_id', 'date'],
    ),
    (
        'ix_fact_traffic_countries_project_domain_country_date',
        ['project_id', 'domain_id', 'country_id', 'date'],
    ),
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, columns in INDEXES:
        op.create_index(index_name, 'fact_traffic_countries_daily', columns)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, _columns in reversed(INDEXES):
        op.drop_index(index_name, table_name='fact_traffic_countries_daily')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
