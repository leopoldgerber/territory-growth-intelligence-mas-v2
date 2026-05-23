"""init db schema

Revision ID: 202605230001
Revises:
Create Date: 2026-05-23 10:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '202605230001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'dim_company',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('normalized_name', sa.Text(), nullable=False),
        sa.Column('is_target_company', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('normalized_name'),
    )
    op.create_table(
        'dim_calendar',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('month_name', sa.Text(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Text(), nullable=False),
        sa.Column('week_of_year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=False),
        sa.Column('is_weekend', sa.Boolean(), nullable=False),
        sa.Column('month_year', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('date'),
    )
    op.create_table(
        'dim_country',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('country_name_en', sa.Text(), nullable=False),
        sa.Column('country_name_ru', sa.Text(), nullable=True),
        sa.Column('iso2', sa.String(length=2), nullable=False),
        sa.Column('iso3', sa.String(length=3), nullable=False),
        sa.Column('tld', sa.Text(), nullable=True),
        sa.Column('region', sa.Text(), nullable=True),
        sa.Column('subregion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iso2'),
        sa.UniqueConstraint('iso3'),
    )
    op.create_table(
        'ingestion_run',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.Text(), nullable=False),
        sa.Column('file_type', sa.Text(), nullable=False),
        sa.Column('source_kind', sa.Text(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column('row_count', sa.BigInteger(), nullable=True),
        sa.Column('company_count', sa.Integer(), nullable=True),
        sa.Column('domain_count', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.Text(), nullable=True),
        sa.Column('ingestion_status', sa.Text(), nullable=False),
        sa.Column('validation_status', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'dim_domain',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('domain', sa.Text(), nullable=False),
        sa.Column('root_domain', sa.Text(), nullable=True),
        sa.Column('tld', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
    )
    op.create_table(
        'fact_traffic_sources_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ingestion_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('domain_id', sa.BigInteger(), nullable=False),
        sa.Column('direct', sa.BigInteger(), nullable=True),
        sa.Column('referral', sa.BigInteger(), nullable=True),
        sa.Column('paid', sa.BigInteger(), nullable=True),
        sa.Column('social', sa.BigInteger(), nullable=True),
        sa.Column('search', sa.BigInteger(), nullable=True),
        sa.Column('calculation_version', sa.Text(), nullable=True),
        sa.Column('source_file_name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['date'], ['dim_calendar.date']),
        sa.ForeignKeyConstraint(['domain_id'], ['dim_domain.id']),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fact_traffic_sources_daily_date', 'fact_traffic_sources_daily', ['date'])
    op.create_index('ix_fact_traffic_sources_daily_company_id', 'fact_traffic_sources_daily', ['company_id'])
    op.create_index('ix_fact_traffic_sources_daily_domain_id', 'fact_traffic_sources_daily', ['domain_id'])
    op.create_index('ix_fact_traffic_sources_daily_project_id', 'fact_traffic_sources_daily', ['project_id'])
    op.create_index(
        'ix_fact_traffic_sources_daily_ingestion_run_id',
        'fact_traffic_sources_daily',
        ['ingestion_run_id'],
    )
    op.create_table(
        'fact_journey_sources_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ingestion_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('domain_id', sa.BigInteger(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('traffic_type', sa.Text(), nullable=True),
        sa.Column('search_source', sa.Text(), nullable=True),
        sa.Column('traffic_share', sa.Numeric(10, 6), nullable=True),
        sa.Column('traffic', sa.BigInteger(), nullable=True),
        sa.Column('changes', sa.Numeric(14, 6), nullable=True),
        sa.Column('calculation_version', sa.Text(), nullable=True),
        sa.Column('source_file_name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['date'], ['dim_calendar.date']),
        sa.ForeignKeyConstraint(['domain_id'], ['dim_domain.id']),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fact_journey_sources_daily_date', 'fact_journey_sources_daily', ['date'])
    op.create_index('ix_fact_journey_sources_daily_company_id', 'fact_journey_sources_daily', ['company_id'])
    op.create_index('ix_fact_journey_sources_daily_domain_id', 'fact_journey_sources_daily', ['domain_id'])
    op.create_index('ix_fact_journey_sources_daily_project_id', 'fact_journey_sources_daily', ['project_id'])
    op.create_index(
        'ix_fact_journey_sources_daily_ingestion_run_id',
        'fact_journey_sources_daily',
        ['ingestion_run_id'],
    )
    op.create_table(
        'fact_device_trends_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ingestion_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('domain_id', sa.BigInteger(), nullable=False),
        sa.Column('visits_devices', sa.BigInteger(), nullable=True),
        sa.Column('visits_desktop', sa.BigInteger(), nullable=True),
        sa.Column('visits_mobile', sa.BigInteger(), nullable=True),
        sa.Column('bounce_desktop_sum', sa.BigInteger(), nullable=True),
        sa.Column('bounce_mobile_sum', sa.BigInteger(), nullable=True),
        sa.Column('bounce_devices', sa.Numeric(10, 6), nullable=True),
        sa.Column('bounce_desktop', sa.Numeric(10, 6), nullable=True),
        sa.Column('bounce_mobile', sa.Numeric(10, 6), nullable=True),
        sa.Column('unique_devices', sa.BigInteger(), nullable=True),
        sa.Column('unique_desktop', sa.BigInteger(), nullable=True),
        sa.Column('unique_mobile', sa.BigInteger(), nullable=True),
        sa.Column('duration_devices', sa.Numeric(12, 4), nullable=True),
        sa.Column('duration_desktop', sa.Numeric(12, 4), nullable=True),
        sa.Column('duration_mobile', sa.Numeric(12, 4), nullable=True),
        sa.Column('all_no_bounce', sa.BigInteger(), nullable=True),
        sa.Column('all_bounce', sa.BigInteger(), nullable=True),
        sa.Column('desktop_no_bounce', sa.BigInteger(), nullable=True),
        sa.Column('desktop_bounce', sa.BigInteger(), nullable=True),
        sa.Column('mobile_no_bounce', sa.BigInteger(), nullable=True),
        sa.Column('mobile_bounce', sa.BigInteger(), nullable=True),
        sa.Column('calculation_version', sa.Text(), nullable=True),
        sa.Column('source_file_name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['date'], ['dim_calendar.date']),
        sa.ForeignKeyConstraint(['domain_id'], ['dim_domain.id']),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fact_device_trends_daily_date', 'fact_device_trends_daily', ['date'])
    op.create_index('ix_fact_device_trends_daily_company_id', 'fact_device_trends_daily', ['company_id'])
    op.create_index('ix_fact_device_trends_daily_domain_id', 'fact_device_trends_daily', ['domain_id'])
    op.create_index('ix_fact_device_trends_daily_project_id', 'fact_device_trends_daily', ['project_id'])
    op.create_index(
        'ix_fact_device_trends_daily_ingestion_run_id',
        'fact_device_trends_daily',
        ['ingestion_run_id'],
    )
    op.create_table(
        'fact_traffic_countries_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ingestion_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('domain_id', sa.BigInteger(), nullable=False),
        sa.Column('country_id', sa.BigInteger(), nullable=False),
        sa.Column('traffic_share', sa.Numeric(10, 6), nullable=True),
        sa.Column('traffic', sa.BigInteger(), nullable=True),
        sa.Column('desktop_share_traffic', sa.BigInteger(), nullable=True),
        sa.Column('mobile_share_traffic', sa.BigInteger(), nullable=True),
        sa.Column('unique_visitors', sa.BigInteger(), nullable=True),
        sa.Column('desktop_share', sa.Numeric(10, 6), nullable=True),
        sa.Column('mobile_share', sa.Numeric(10, 6), nullable=True),
        sa.Column('pages_per_visit', sa.Numeric(10, 4), nullable=True),
        sa.Column('avg_visit_duration', sa.Numeric(12, 4), nullable=True),
        sa.Column('bounce_rate', sa.Numeric(10, 6), nullable=True),
        sa.Column('traffic_no_bounce', sa.BigInteger(), nullable=True),
        sa.Column('traffic_bounce', sa.BigInteger(), nullable=True),
        sa.Column('desktop', sa.BigInteger(), nullable=True),
        sa.Column('mobile', sa.BigInteger(), nullable=True),
        sa.Column('calculation_version', sa.Text(), nullable=True),
        sa.Column('source_file_name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_company.id']),
        sa.ForeignKeyConstraint(['country_id'], ['dim_country.id']),
        sa.ForeignKeyConstraint(['date'], ['dim_calendar.date']),
        sa.ForeignKeyConstraint(['domain_id'], ['dim_domain.id']),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fact_traffic_countries_daily_date', 'fact_traffic_countries_daily', ['date'])
    op.create_index('ix_fact_traffic_countries_daily_company_id', 'fact_traffic_countries_daily', ['company_id'])
    op.create_index('ix_fact_traffic_countries_daily_domain_id', 'fact_traffic_countries_daily', ['domain_id'])
    op.create_index('ix_fact_traffic_countries_daily_country_id', 'fact_traffic_countries_daily', ['country_id'])
    op.create_index('ix_fact_traffic_countries_daily_project_id', 'fact_traffic_countries_daily', ['project_id'])
    op.create_index(
        'ix_fact_traffic_countries_daily_ingestion_run_id',
        'fact_traffic_countries_daily',
        ['ingestion_run_id'],
    )
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_fact_traffic_countries_daily_ingestion_run_id', table_name='fact_traffic_countries_daily')
    op.drop_index('ix_fact_traffic_countries_daily_project_id', table_name='fact_traffic_countries_daily')
    op.drop_index('ix_fact_traffic_countries_daily_country_id', table_name='fact_traffic_countries_daily')
    op.drop_index('ix_fact_traffic_countries_daily_domain_id', table_name='fact_traffic_countries_daily')
    op.drop_index('ix_fact_traffic_countries_daily_company_id', table_name='fact_traffic_countries_daily')
    op.drop_index('ix_fact_traffic_countries_daily_date', table_name='fact_traffic_countries_daily')
    op.drop_index('ix_fact_device_trends_daily_ingestion_run_id', table_name='fact_device_trends_daily')
    op.drop_index('ix_fact_device_trends_daily_project_id', table_name='fact_device_trends_daily')
    op.drop_index('ix_fact_device_trends_daily_domain_id', table_name='fact_device_trends_daily')
    op.drop_index('ix_fact_device_trends_daily_company_id', table_name='fact_device_trends_daily')
    op.drop_index('ix_fact_device_trends_daily_date', table_name='fact_device_trends_daily')
    op.drop_index('ix_fact_journey_sources_daily_ingestion_run_id', table_name='fact_journey_sources_daily')
    op.drop_index('ix_fact_journey_sources_daily_project_id', table_name='fact_journey_sources_daily')
    op.drop_index('ix_fact_journey_sources_daily_domain_id', table_name='fact_journey_sources_daily')
    op.drop_index('ix_fact_journey_sources_daily_company_id', table_name='fact_journey_sources_daily')
    op.drop_index('ix_fact_journey_sources_daily_date', table_name='fact_journey_sources_daily')
    op.drop_index('ix_fact_traffic_sources_daily_ingestion_run_id', table_name='fact_traffic_sources_daily')
    op.drop_index('ix_fact_traffic_sources_daily_project_id', table_name='fact_traffic_sources_daily')
    op.drop_index('ix_fact_traffic_sources_daily_domain_id', table_name='fact_traffic_sources_daily')
    op.drop_index('ix_fact_traffic_sources_daily_company_id', table_name='fact_traffic_sources_daily')
    op.drop_index('ix_fact_traffic_sources_daily_date', table_name='fact_traffic_sources_daily')
    op.drop_table('fact_traffic_countries_daily')
    op.drop_table('fact_device_trends_daily')
    op.drop_table('fact_journey_sources_daily')
    op.drop_table('fact_traffic_sources_daily')
    op.drop_table('dim_domain')
    op.drop_table('ingestion_run')
    op.drop_table('dim_country')
    op.drop_table('dim_calendar')
    op.drop_table('dim_company')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
