"""add project channel region dims

Revision ID: 202606160001
Revises: 202605310001
Create Date: 2026-06-16 21:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606160001'
down_revision: str | None = '202605310001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_PROJECT_ID = '00000000-0000-0000-0000-000000000001'
PROJECT_TABLES = (
    'ingestion_run',
    'fact_traffic_countries_daily',
    'fact_traffic_sources_daily',
    'fact_journey_sources_daily',
    'fact_device_trends_daily',
)


def create_project() -> str:
    """Create project table.
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
    return 'created'


def seed_project() -> str:
    """Seed project records.
    Args:
        None (None): No arguments are required."""
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
        ON CONFLICT (id) DO UPDATE
        SET
            name = EXCLUDED.name,
            slug = EXCLUDED.slug,
            description = EXCLUDED.description,
            status = EXCLUDED.status,
            is_default = EXCLUDED.is_default,
            updated_at = now()
        """
    )
    for table_name in PROJECT_TABLES:
        op.execute(
            f"""
            INSERT INTO project (id, name, slug, description, status, is_default, created_at, updated_at)
            SELECT DISTINCT
                project_id,
                'Imported Project ' || project_id::text,
                'imported-' || replace(project_id::text, '-', ''),
                'Created from existing project_id values during migration.',
                'active',
                false,
                now(),
                now()
            FROM {table_name}
            WHERE project_id IS NOT NULL
                AND project_id <> '{DEFAULT_PROJECT_ID}'
            ON CONFLICT (id) DO NOTHING
            """
        )
    return 'seeded'


def create_channels() -> str:
    """Create channel table.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'dim_channel',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_paid', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    channel_table = sa.table(
        'dim_channel',
        sa.column('id', sa.BigInteger()),
        sa.column('code', sa.Text()),
        sa.column('name', sa.Text()),
        sa.column('description', sa.Text()),
        sa.column('is_paid', sa.Boolean()),
        sa.column('sort_order', sa.Integer()),
        sa.column('is_active', sa.Boolean()),
    )
    op.bulk_insert(
        channel_table,
        [
            {
                'id': 1,
                'code': 'direct',
                'name': 'Direct',
                'description': 'Direct traffic channel.',
                'is_paid': False,
                'sort_order': 10,
                'is_active': True,
            },
            {
                'id': 2,
                'code': 'referral',
                'name': 'Referral',
                'description': 'Referral traffic channel.',
                'is_paid': False,
                'sort_order': 20,
                'is_active': True,
            },
            {
                'id': 3,
                'code': 'paid',
                'name': 'Paid',
                'description': 'Paid traffic channel.',
                'is_paid': True,
                'sort_order': 30,
                'is_active': True,
            },
            {
                'id': 4,
                'code': 'social',
                'name': 'Social',
                'description': 'Social traffic channel.',
                'is_paid': False,
                'sort_order': 40,
                'is_active': True,
            },
            {
                'id': 5,
                'code': 'search',
                'name': 'Search',
                'description': 'Search traffic channel.',
                'is_paid': False,
                'sort_order': 50,
                'is_active': True,
            },
        ],
    )
    return 'created'


def create_regions() -> str:
    """Create region tables.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'dim_region',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('region_type', sa.Text(), nullable=False),
        sa.Column('parent_region_id', sa.BigInteger(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_region_id'], ['dim_region.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    region_table = sa.table(
        'dim_region',
        sa.column('id', sa.BigInteger()),
        sa.column('code', sa.Text()),
        sa.column('name', sa.Text()),
        sa.column('region_type', sa.Text()),
        sa.column('parent_region_id', sa.BigInteger()),
        sa.column('description', sa.Text()),
        sa.column('sort_order', sa.Integer()),
        sa.column('is_active', sa.Boolean()),
    )
    op.bulk_insert(
        region_table,
        [
            {
                'id': 1,
                'code': 'europe',
                'name': 'Europe',
                'region_type': 'geographic',
                'parent_region_id': None,
                'description': 'European region.',
                'sort_order': 10,
                'is_active': True,
            },
            {
                'id': 2,
                'code': 'latam',
                'name': 'LATAM',
                'region_type': 'geographic',
                'parent_region_id': None,
                'description': 'Latin America region.',
                'sort_order': 20,
                'is_active': True,
            },
            {
                'id': 3,
                'code': 'cis',
                'name': 'CIS',
                'region_type': 'geographic',
                'parent_region_id': None,
                'description': 'Commonwealth of Independent States region.',
                'sort_order': 30,
                'is_active': True,
            },
            {
                'id': 4,
                'code': 'north_america',
                'name': 'North America',
                'region_type': 'geographic',
                'parent_region_id': None,
                'description': 'North America region.',
                'sort_order': 40,
                'is_active': True,
            },
            {
                'id': 5,
                'code': 'western_europe',
                'name': 'Western Europe',
                'region_type': 'geographic',
                'parent_region_id': 1,
                'description': 'Western Europe subregion.',
                'sort_order': 50,
                'is_active': True,
            },
            {
                'id': 6,
                'code': 'tier_1',
                'name': 'Tier-1',
                'region_type': 'business',
                'parent_region_id': None,
                'description': 'Tier-1 business market group.',
                'sort_order': 60,
                'is_active': True,
            },
            {
                'id': 7,
                'code': 'other',
                'name': 'Other',
                'region_type': 'custom',
                'parent_region_id': None,
                'description': 'Fallback market group.',
                'sort_order': 70,
                'is_active': True,
            },
        ],
    )
    op.create_table(
        'dim_country_region',
        sa.Column('country_id', sa.BigInteger(), nullable=False),
        sa.Column('region_id', sa.BigInteger(), nullable=False),
        sa.Column('relation_type', sa.Text(), server_default='membership', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['region_id'], ['dim_region.id']),
        sa.PrimaryKeyConstraint('country_id', 'region_id', 'relation_type'),
    )
    op.create_index('ix_dim_country_region_country_id', 'dim_country_region', ['country_id'])
    op.create_index('ix_dim_country_region_region_id', 'dim_country_region', ['region_id'])
    return 'created'


def create_foreign_keys() -> str:
    """Create project foreign keys.
    Args:
        None (None): No arguments are required."""
    op.create_foreign_key('fk_ingestion_run_project_id_project', 'ingestion_run', 'project', ['project_id'], ['id'])
    op.create_foreign_key(
        'fk_fact_traffic_countries_daily_project_id_project',
        'fact_traffic_countries_daily',
        'project',
        ['project_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_fact_traffic_sources_daily_project_id_project',
        'fact_traffic_sources_daily',
        'project',
        ['project_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_fact_journey_sources_daily_project_id_project',
        'fact_journey_sources_daily',
        'project',
        ['project_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_fact_device_trends_daily_project_id_project',
        'fact_device_trends_daily',
        'project',
        ['project_id'],
        ['id'],
    )
    return 'created'


def drop_foreign_keys() -> str:
    """Drop project foreign keys.
    Args:
        None (None): No arguments are required."""
    op.drop_constraint(
        'fk_fact_device_trends_daily_project_id_project',
        'fact_device_trends_daily',
        type_='foreignkey',
    )
    op.drop_constraint(
        'fk_fact_journey_sources_daily_project_id_project',
        'fact_journey_sources_daily',
        type_='foreignkey',
    )
    op.drop_constraint(
        'fk_fact_traffic_sources_daily_project_id_project',
        'fact_traffic_sources_daily',
        type_='foreignkey',
    )
    op.drop_constraint(
        'fk_fact_traffic_countries_daily_project_id_project',
        'fact_traffic_countries_daily',
        type_='foreignkey',
    )
    op.drop_constraint('fk_ingestion_run_project_id_project', 'ingestion_run', type_='foreignkey')
    return 'dropped'


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    create_project()
    seed_project()
    create_channels()
    create_regions()
    create_foreign_keys()
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    drop_foreign_keys()
    op.drop_index('ix_dim_country_region_region_id', table_name='dim_country_region')
    op.drop_index('ix_dim_country_region_country_id', table_name='dim_country_region')
    op.drop_table('dim_country_region')
    op.drop_table('dim_region')
    op.drop_table('dim_channel')
    op.drop_table('project')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
