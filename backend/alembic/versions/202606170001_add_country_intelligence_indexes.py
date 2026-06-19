"""add country intelligence indexes

Revision ID: 202606170001
Revises: 202606160001
Create Date: 2026-06-17 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '202606170001'
down_revision: str | None = '202606160001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    ('ix_fact_traffic_countries_project_date', ['project_id', 'date']),
    ('ix_fact_traffic_countries_project_country_date', ['project_id', 'country_id', 'date']),
    ('ix_fact_traffic_countries_project_domain_date', ['project_id', 'domain_id', 'date']),
    ('ix_fact_traffic_countries_project_company_date', ['project_id', 'company_id', 'date']),
    (
        'ix_fact_traffic_countries_project_country_domain_date',
        ['project_id', 'country_id', 'domain_id', 'date'],
    ),
    ('ix_dim_company_name', ['name']),
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, columns in INDEXES:
        table_name = 'dim_company' if index_name == 'ix_dim_company_name' else 'fact_traffic_countries_daily'
        op.create_index(index_name, table_name, columns)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, _columns in reversed(INDEXES):
        table_name = 'dim_company' if index_name == 'ix_dim_company_name' else 'fact_traffic_countries_daily'
        op.drop_index(index_name, table_name=table_name)
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
