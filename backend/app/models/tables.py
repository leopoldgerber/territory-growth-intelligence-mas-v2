from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DimCompany(Base):
    __tablename__ = 'dim_company'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_target_company: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DimDomain(Base):
    __tablename__ = 'dim_domain'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('dim_company.id'), nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    root_domain: Mapped[str | None] = mapped_column(Text)
    tld: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DimCountry(Base):
    __tablename__ = 'dim_country'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    country_name_en: Mapped[str] = mapped_column(Text, nullable=False)
    country_name_ru: Mapped[str | None] = mapped_column(Text)
    iso2: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    iso3: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    tld: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    subregion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DimChannel(Base):
    __tablename__ = 'dim_channel'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DimRegion(Base):
    __tablename__ = 'dim_region'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    region_type: Mapped[str] = mapped_column(Text, nullable=False)
    parent_region_id: Mapped[int | None] = mapped_column(ForeignKey('dim_region.id'))
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DimCountryRegion(Base):
    __tablename__ = 'dim_country_region'
    __table_args__ = (
        Index('ix_dim_country_region_country_id', 'country_id'),
        Index('ix_dim_country_region_region_id', 'region_id'),
    )

    country_id: Mapped[int] = mapped_column(ForeignKey('dim_country.id'), primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey('dim_region.id'), primary_key=True)
    relation_type: Mapped[str] = mapped_column(Text, primary_key=True, default='membership')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DimCalendar(Base):
    __tablename__ = 'dim_calendar'

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    month_name: Mapped[str] = mapped_column(Text, nullable=False)
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[str] = mapped_column(Text, nullable=False)
    week_of_year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False)
    month_year: Mapped[date] = mapped_column(Date, nullable=False)


class IngestionRun(Base):
    __tablename__ = 'ingestion_run'

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    stored_file_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    progress_stage: Mapped[str | None] = mapped_column(Text)
    progress_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    row_count: Mapped[int | None] = mapped_column(BigInteger)
    valid_row_count: Mapped[int | None] = mapped_column(BigInteger)
    invalid_row_count: Mapped[int | None] = mapped_column(BigInteger)
    inserted_row_count: Mapped[int | None] = mapped_column(BigInteger)
    skipped_duplicate_count: Mapped[int | None] = mapped_column(BigInteger)
    failed_row_count: Mapped[int | None] = mapped_column(BigInteger)
    company_count: Mapped[int | None] = mapped_column(Integer)
    domain_count: Mapped[int | None] = mapped_column(Integer)
    country_count: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(Text)
    ingestion_status: Mapped[str] = mapped_column(Text, nullable=False)
    validation_status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    worker_name: Mapped[str | None] = mapped_column(Text)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IngestionValidationError(Base):
    __tablename__ = 'ingestion_validation_error'
    __table_args__ = (
        Index('ix_ingestion_validation_error_ingestion_run_id', 'ingestion_run_id'),
        Index('ix_ingestion_validation_error_error_code', 'error_code'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey('ingestion_run.id'), nullable=False)
    row_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    column_name: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FactTrafficCountriesDaily(Base):
    __tablename__ = 'fact_traffic_countries_daily'
    __table_args__ = (
        Index('ix_fact_traffic_countries_daily_date', 'date'),
        Index('ix_fact_traffic_countries_daily_company_id', 'company_id'),
        Index('ix_fact_traffic_countries_daily_domain_id', 'domain_id'),
        Index('ix_fact_traffic_countries_daily_country_id', 'country_id'),
        Index('ix_fact_traffic_countries_daily_project_id', 'project_id'),
        Index('ix_fact_traffic_countries_daily_ingestion_run_id', 'ingestion_run_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey('ingestion_run.id'), nullable=False)
    date: Mapped[date] = mapped_column(ForeignKey('dim_calendar.date'), nullable=False)
    day: Mapped[int | None] = mapped_column(Integer)
    day_of_week: Mapped[str | None] = mapped_column(Text)
    week_of_year: Mapped[int | None] = mapped_column(Integer)
    is_weekend: Mapped[bool | None] = mapped_column(Boolean)
    month: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    month_number: Mapped[int | None] = mapped_column(Integer)
    month_year: Mapped[date | None] = mapped_column(Date)
    company_id: Mapped[int] = mapped_column(ForeignKey('dim_company.id'), nullable=False)
    domain_id: Mapped[int] = mapped_column(ForeignKey('dim_domain.id'), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey('dim_country.id'), nullable=False)
    traffic_share: Mapped[float | None] = mapped_column(Numeric(10, 6))
    traffic: Mapped[int | None] = mapped_column(BigInteger)
    desktop_share_traffic: Mapped[int | None] = mapped_column(BigInteger)
    mobile_share_traffic: Mapped[int | None] = mapped_column(BigInteger)
    unique_visitors: Mapped[int | None] = mapped_column(BigInteger)
    desktop_share: Mapped[float | None] = mapped_column(Numeric(10, 6))
    mobile_share: Mapped[float | None] = mapped_column(Numeric(10, 6))
    pages_per_visit: Mapped[float | None] = mapped_column(Numeric(10, 4))
    avg_visit_duration: Mapped[float | None] = mapped_column(Numeric(12, 4))
    bounce_rate: Mapped[float | None] = mapped_column(Numeric(10, 6))
    traffic_no_bounce: Mapped[int | None] = mapped_column(BigInteger)
    traffic_bounce: Mapped[int | None] = mapped_column(BigInteger)
    desktop: Mapped[int | None] = mapped_column(BigInteger)
    mobile: Mapped[int | None] = mapped_column(BigInteger)
    calculation_version: Mapped[str | None] = mapped_column(Text)
    source_file_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FactTrafficSourcesDaily(Base):
    __tablename__ = 'fact_traffic_sources_daily'
    __table_args__ = (
        Index('ix_fact_traffic_sources_daily_date', 'date'),
        Index('ix_fact_traffic_sources_daily_company_id', 'company_id'),
        Index('ix_fact_traffic_sources_daily_domain_id', 'domain_id'),
        Index('ix_fact_traffic_sources_daily_project_id', 'project_id'),
        Index('ix_fact_traffic_sources_daily_ingestion_run_id', 'ingestion_run_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey('ingestion_run.id'), nullable=False)
    date: Mapped[date] = mapped_column(ForeignKey('dim_calendar.date'), nullable=False)
    day: Mapped[int | None] = mapped_column(Integer)
    day_of_week: Mapped[str | None] = mapped_column(Text)
    week_of_year: Mapped[int | None] = mapped_column(Integer)
    is_weekend: Mapped[bool | None] = mapped_column(Boolean)
    month: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    month_number: Mapped[int | None] = mapped_column(Integer)
    month_year: Mapped[date | None] = mapped_column(Date)
    company_id: Mapped[int] = mapped_column(ForeignKey('dim_company.id'), nullable=False)
    domain_id: Mapped[int] = mapped_column(ForeignKey('dim_domain.id'), nullable=False)
    direct: Mapped[int | None] = mapped_column(BigInteger)
    referral: Mapped[int | None] = mapped_column(BigInteger)
    paid: Mapped[int | None] = mapped_column(BigInteger)
    social: Mapped[int | None] = mapped_column(BigInteger)
    search: Mapped[int | None] = mapped_column(BigInteger)
    calculation_version: Mapped[str | None] = mapped_column(Text)
    source_file_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FactJourneySourcesDaily(Base):
    __tablename__ = 'fact_journey_sources_daily'
    __table_args__ = (
        Index('ix_fact_journey_sources_daily_date', 'date'),
        Index('ix_fact_journey_sources_daily_company_id', 'company_id'),
        Index('ix_fact_journey_sources_daily_domain_id', 'domain_id'),
        Index('ix_fact_journey_sources_daily_project_id', 'project_id'),
        Index('ix_fact_journey_sources_daily_ingestion_run_id', 'ingestion_run_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey('ingestion_run.id'), nullable=False)
    date: Mapped[date] = mapped_column(ForeignKey('dim_calendar.date'), nullable=False)
    day: Mapped[int | None] = mapped_column(Integer)
    day_of_week: Mapped[str | None] = mapped_column(Text)
    week_of_year: Mapped[int | None] = mapped_column(Integer)
    is_weekend: Mapped[bool | None] = mapped_column(Boolean)
    month: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    month_number: Mapped[int | None] = mapped_column(Integer)
    month_year: Mapped[date | None] = mapped_column(Date)
    company_id: Mapped[int] = mapped_column(ForeignKey('dim_company.id'), nullable=False)
    domain_id: Mapped[int] = mapped_column(ForeignKey('dim_domain.id'), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    traffic_type: Mapped[str | None] = mapped_column(Text)
    search_source: Mapped[str | None] = mapped_column(Text)
    traffic_share: Mapped[float | None] = mapped_column(Numeric(10, 6))
    traffic: Mapped[int | None] = mapped_column(BigInteger)
    changes: Mapped[float | None] = mapped_column(Numeric(14, 6))
    calculation_version: Mapped[str | None] = mapped_column(Text)
    source_file_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FactDeviceTrendsDaily(Base):
    __tablename__ = 'fact_device_trends_daily'
    __table_args__ = (
        Index('ix_fact_device_trends_daily_date', 'date'),
        Index('ix_fact_device_trends_daily_company_id', 'company_id'),
        Index('ix_fact_device_trends_daily_domain_id', 'domain_id'),
        Index('ix_fact_device_trends_daily_project_id', 'project_id'),
        Index('ix_fact_device_trends_daily_ingestion_run_id', 'ingestion_run_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey('ingestion_run.id'), nullable=False)
    date: Mapped[date] = mapped_column(ForeignKey('dim_calendar.date'), nullable=False)
    day: Mapped[int | None] = mapped_column(Integer)
    day_of_week: Mapped[str | None] = mapped_column(Text)
    week_of_year: Mapped[int | None] = mapped_column(Integer)
    is_weekend: Mapped[bool | None] = mapped_column(Boolean)
    month: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    month_number: Mapped[int | None] = mapped_column(Integer)
    month_year: Mapped[date | None] = mapped_column(Date)
    company_id: Mapped[int] = mapped_column(ForeignKey('dim_company.id'), nullable=False)
    domain_id: Mapped[int] = mapped_column(ForeignKey('dim_domain.id'), nullable=False)
    visits_devices: Mapped[int | None] = mapped_column(BigInteger)
    visits_desktop: Mapped[int | None] = mapped_column(BigInteger)
    visits_mobile: Mapped[int | None] = mapped_column(BigInteger)
    bounce_desktop_sum: Mapped[int | None] = mapped_column(BigInteger)
    bounce_mobile_sum: Mapped[int | None] = mapped_column(BigInteger)
    bounce_devices: Mapped[float | None] = mapped_column(Numeric(10, 6))
    bounce_desktop: Mapped[float | None] = mapped_column(Numeric(10, 6))
    bounce_mobile: Mapped[float | None] = mapped_column(Numeric(10, 6))
    unique_devices: Mapped[int | None] = mapped_column(BigInteger)
    unique_desktop: Mapped[int | None] = mapped_column(BigInteger)
    unique_mobile: Mapped[int | None] = mapped_column(BigInteger)
    duration_devices: Mapped[float | None] = mapped_column(Numeric(12, 4))
    duration_desktop: Mapped[float | None] = mapped_column(Numeric(12, 4))
    duration_mobile: Mapped[float | None] = mapped_column(Numeric(12, 4))
    all_no_bounce: Mapped[int | None] = mapped_column(BigInteger)
    all_bounce: Mapped[int | None] = mapped_column(BigInteger)
    desktop_no_bounce: Mapped[int | None] = mapped_column(BigInteger)
    desktop_bounce: Mapped[int | None] = mapped_column(BigInteger)
    mobile_no_bounce: Mapped[int | None] = mapped_column(BigInteger)
    mobile_bounce: Mapped[int | None] = mapped_column(BigInteger)
    calculation_version: Mapped[str | None] = mapped_column(Text)
    source_file_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
