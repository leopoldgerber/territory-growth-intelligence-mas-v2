"""add channel intelligence indexes

Revision ID: 202606210001
Revises: 202606190001
Create Date: 2026-06-21 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '202606210001'
down_revision: str | None = '202606190001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    ('ix_fact_traffic_sources_project_date', 'fact_traffic_sources_daily', ['project_id', 'date']),
    (
        'ix_fact_traffic_sources_project_company_date',
        'fact_traffic_sources_daily',
        ['project_id', 'company_id', 'date'],
    ),
    (
        'ix_fact_traffic_sources_project_domain_date',
        'fact_traffic_sources_daily',
        ['project_id', 'domain_id', 'date'],
    ),
    (
        'ix_fact_traffic_sources_project_company_domain_date',
        'fact_traffic_sources_daily',
        ['project_id', 'company_id', 'domain_id', 'date'],
    ),
    ('ix_fact_journey_sources_project_date', 'fact_journey_sources_daily', ['project_id', 'date']),
    (
        'ix_fact_journey_sources_project_company_date',
        'fact_journey_sources_daily',
        ['project_id', 'company_id', 'date'],
    ),
    (
        'ix_fact_journey_sources_project_domain_date',
        'fact_journey_sources_daily',
        ['project_id', 'domain_id', 'date'],
    ),
    (
        'ix_fact_journey_sources_project_source_date',
        'fact_journey_sources_daily',
        ['project_id', 'source_type', 'date'],
    ),
    (
        'ix_fact_journey_sources_project_traffic_date',
        'fact_journey_sources_daily',
        ['project_id', 'traffic_type', 'date'],
    ),
    (
        'ix_fact_journey_sources_project_search_date',
        'fact_journey_sources_daily',
        ['project_id', 'search_source', 'date'],
    ),
    (
        'ix_fact_traffic_countries_project_country_company_domain_date',
        'fact_traffic_countries_daily',
        ['project_id', 'country_id', 'company_id', 'domain_id', 'date'],
    ),
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, table_name, columns in INDEXES:
        op.create_index(index_name, table_name, columns)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, table_name, _columns in reversed(INDEXES):
        op.drop_index(index_name, table_name=table_name)
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
