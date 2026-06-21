"""add device intelligence indexes

Revision ID: 202606210002
Revises: 202606210001
Create Date: 2026-06-21 14:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '202606210002'
down_revision: str | None = '202606210001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    ('ix_fact_device_trends_project_date', ['project_id', 'date']),
    ('ix_fact_device_trends_project_company_date', ['project_id', 'company_id', 'date']),
    ('ix_fact_device_trends_project_domain_date', ['project_id', 'domain_id', 'date']),
    (
        'ix_fact_device_trends_project_company_domain_date',
        ['project_id', 'company_id', 'domain_id', 'date'],
    ),
)


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, columns in INDEXES:
        op.create_index(index_name, 'fact_device_trends_daily', columns)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    for index_name, _columns in reversed(INDEXES):
        op.drop_index(index_name, table_name='fact_device_trends_daily')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
