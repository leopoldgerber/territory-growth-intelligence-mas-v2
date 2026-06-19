"""remove project entity

Revision ID: 202606170002
Revises: 202606170001
Create Date: 2026-06-17 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606170002'
down_revision: str | None = '202606170001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROJECT_FOREIGN_KEYS = (
    ('fk_ingestion_run_project_id_project', 'ingestion_run'),
    ('fk_fact_traffic_countries_daily_project_id_project', 'fact_traffic_countries_daily'),
    ('fk_fact_traffic_sources_daily_project_id_project', 'fact_traffic_sources_daily'),
    ('fk_fact_journey_sources_daily_project_id_project', 'fact_journey_sources_daily'),
    ('fk_fact_device_trends_daily_project_id_project', 'fact_device_trends_daily'),
)

DEFAULT_PROJECT_ID = '00000000-0000-0000-0000-000000000001'


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    for constraint_name, table_name in PROJECT_FOREIGN_KEYS:
        op.drop_constraint(constraint_name, table_name, type_='foreignkey')
    op.drop_table('project')
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'project',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), server_default='active', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.execute(
        f"""
        INSERT INTO project (id, name, slug, description, status, is_default, created_at, updated_at)
        VALUES (
            '{DEFAULT_PROJECT_ID}',
            'Territory Growth Intelligence Local',
            'default',
            'Default local project.',
            'active',
            true,
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING
        """
    )
    for constraint_name, table_name in reversed(PROJECT_FOREIGN_KEYS):
        op.create_foreign_key(constraint_name, table_name, 'project', ['project_id'], ['id'])
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
