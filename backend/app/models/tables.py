from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
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


class DerivedSignal(Base):
    __tablename__ = 'derived_signal'
    __table_args__ = (
        Index('ix_derived_signal_project_type', 'project_id', 'signal_type'),
        Index('ix_derived_signal_project_group', 'project_id', 'signal_group'),
        Index('ix_derived_signal_project_entity', 'project_id', 'entity_type'),
        Index('ix_derived_signal_project_country', 'project_id', 'country_id'),
        Index('ix_derived_signal_project_company', 'project_id', 'company_id'),
        Index('ix_derived_signal_project_domain', 'project_id', 'domain_id'),
        Index('ix_derived_signal_project_period', 'project_id', 'date_from', 'date_to'),
        Index('ix_derived_signal_project_severity', 'project_id', 'severity'),
        Index('ix_derived_signal_project_scope', 'project_id', 'scope'),
        Index('ix_derived_signal_context_hash', 'context_hash'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    signal_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    context_hash: Mapped[str | None] = mapped_column(Text)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    signal_type: Mapped[str] = mapped_column(Text, nullable=False)
    signal_group: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    domain_id: Mapped[int | None] = mapped_column(ForeignKey('dim_domain.id'))
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    period_grain: Mapped[str] = mapped_column(Text, nullable=False, default='custom')
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False, default='overall')
    score: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    baseline_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    delta_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    delta_percent: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    calculation_version: Mapped[str] = mapped_column(Text, nullable=False, default='v1')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OpportunityScore(Base):
    __tablename__ = 'opportunity_score'
    __table_args__ = (
        Index('ix_opportunity_score_project_period', 'project_id', 'date_from', 'date_to'),
        Index('ix_opportunity_score_project_scope', 'project_id', 'scope'),
        Index('ix_opportunity_score_project_country', 'project_id', 'country_id'),
        Index('ix_opportunity_score_project_score', 'project_id', 'opportunity_score'),
        Index('ix_opportunity_score_project_category', 'project_id', 'score_category'),
        Index('ix_opportunity_score_project_version', 'project_id', 'calculation_version'),
        Index('ix_opportunity_score_context_hash', 'context_hash'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    context_hash: Mapped[str | None] = mapped_column(Text)
    context_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    country_id: Mapped[int] = mapped_column(ForeignKey('dim_country.id'), nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    score_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    score_category: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer)
    market_size_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    growth_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    traffic_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    competition_level_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    concentration_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    channel_stability_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    entry_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    position_potential_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    strengths: Mapped[list[str] | None] = mapped_column(JSONB)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSONB)
    risks: Mapped[list[str] | None] = mapped_column(JSONB)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    calculation_version: Mapped[str] = mapped_column(Text, nullable=False, default='v1')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BudgetStrategyReport(Base):
    __tablename__ = 'budget_strategy_report'
    __table_args__ = (
        Index('ix_budget_strategy_project_period', 'project_id', 'date_from', 'date_to'),
        Index('ix_budget_strategy_project_country', 'project_id', 'country_id'),
        Index('ix_budget_strategy_project_scope', 'project_id', 'scope'),
        Index('ix_budget_strategy_project_created', 'project_id', 'created_at'),
        Index('ix_budget_strategy_project_version', 'project_id', 'calculation_version'),
        Index('ix_budget_strategy_project_mode', 'project_id', 'strategy_mode'),
        Index('ix_budget_strategy_context_hash', 'context_hash'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey('dim_country.id'), nullable=False)
    strategy_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)
    strategy_mode: Mapped[str] = mapped_column(Text, nullable=False, default='existing_presence')
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='generated')
    opportunity_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    opportunity_score_id: Mapped[int | None] = mapped_column(ForeignKey('opportunity_score.id'))
    recommended_approach: Mapped[str] = mapped_column(Text, nullable=False)
    allocation: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    channel_roles: Mapped[dict[str, list[str]]] = mapped_column(JSONB, nullable=False)
    expected_effect: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    risks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dependency_status: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    context_hash: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    calculation_version: Mapped[str] = mapped_column(Text, nullable=False, default='v1')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MasRun(Base):
    __tablename__ = 'mas_run'
    __table_args__ = (
        Index('ix_mas_run_project_created', 'project_id', 'created_at'),
        Index('ix_mas_run_project_status', 'project_id', 'status'),
        Index('ix_mas_run_country', 'country_id'),
        Index('ix_mas_run_company', 'company_id'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    created_by: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='pending')
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_intent: Mapped[str | None] = mapped_column(Text)
    resolved_context_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    strategy_mode: Mapped[str | None] = mapped_column(Text)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(Text)
    default_llm_provider: Mapped[str | None] = mapped_column(Text)
    default_llm_model: Mapped[str | None] = mapped_column(Text)
    prompt_version_id: Mapped[int | None] = mapped_column(ForeignKey('mas_prompt_version.id'))
    rag_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rag_status: Mapped[str | None] = mapped_column(Text)
    rag_results_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    planner_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    synthesis_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    final_answer: Mapped[str | None] = mapped_column(Text)
    final_summary: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MasAgentRun(Base):
    __tablename__ = 'mas_agent_run'
    __table_args__ = (
        Index('ix_mas_agent_run_mas_run_id', 'mas_run_id'),
        Index('ix_mas_agent_run_name', 'agent_name'),
        Index('ix_mas_agent_run_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    mas_run_id: Mapped[UUID] = mapped_column(ForeignKey('mas_run.id'), nullable=False)
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='pending')
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MasToolCall(Base):
    __tablename__ = 'mas_tool_call'
    __table_args__ = (
        Index('ix_mas_tool_call_mas_run_id', 'mas_run_id'),
        Index('ix_mas_tool_call_agent_run_id', 'agent_run_id'),
        Index('ix_mas_tool_call_name', 'tool_name'),
        Index('ix_mas_tool_call_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    mas_run_id: Mapped[UUID] = mapped_column(ForeignKey('mas_run.id'), nullable=False)
    agent_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_agent_run.id'))
    tool_name: Mapped[str] = mapped_column(Text, nullable=False)
    tool_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='pending')
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MasEvidenceItem(Base):
    __tablename__ = 'mas_evidence_item'
    __table_args__ = (
        Index('ix_mas_evidence_item_mas_run_id', 'mas_run_id'),
        Index('ix_mas_evidence_item_source_type', 'source_type'),
        Index('ix_mas_evidence_item_evidence_type', 'evidence_type'),
        Index('ix_mas_evidence_item_context_hash', 'context_hash'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    mas_run_id: Mapped[UUID] = mapped_column(ForeignKey('mas_run.id'), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_table: Mapped[str | None] = mapped_column(Text)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    context_hash: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MasEvidencePack(Base):
    __tablename__ = 'mas_evidence_pack'
    __table_args__ = (
        Index('ix_mas_evidence_pack_mas_run_id', 'mas_run_id'),
        Index('ix_mas_evidence_pack_context_hash', 'context_hash'),
        Index('ix_mas_evidence_pack_created_at', 'created_at'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    mas_run_id: Mapped[UUID] = mapped_column(ForeignKey('mas_run.id'), nullable=False)
    context_hash: Mapped[str | None] = mapped_column(Text)
    pack_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    llm_context_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    quality_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MasPromptVersion(Base):
    __tablename__ = 'mas_prompt_version'
    __table_args__ = (
        Index('ix_mas_prompt_version_key_active', 'prompt_key', 'is_active'),
        Index('ix_mas_prompt_version_key_version', 'prompt_key', 'version', unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prompt_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    user_prompt_template: Mapped[str | None] = mapped_column(Text)
    output_schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MasModelProvider(Base):
    __tablename__ = 'mas_model_provider'
    __table_args__ = (
        Index('ix_mas_model_provider_role_active', 'model_role', 'is_active'),
        Index('ix_mas_model_provider_provider_model', 'provider', 'model_name'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    model_role: Mapped[str] = mapped_column(Text, nullable=False)
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MasModelCall(Base):
    __tablename__ = 'mas_model_call'
    __table_args__ = (
        Index('ix_mas_model_call_mas_run_id', 'mas_run_id'),
        Index('ix_mas_model_call_agent_run_id', 'agent_run_id'),
        Index('ix_mas_model_call_prompt_version_id', 'prompt_version_id'),
        Index('ix_mas_model_call_provider_model', 'provider', 'model_name'),
        Index('ix_mas_model_call_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    mas_run_id: Mapped[UUID] = mapped_column(ForeignKey('mas_run.id'), nullable=False)
    agent_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_agent_run.id'))
    prompt_version_id: Mapped[int | None] = mapped_column(ForeignKey('mas_prompt_version.id'))
    prompt_key: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    structured_output_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    raw_response_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KnowledgeDocument(Base):
    __tablename__ = 'knowledge_document'
    __table_args__ = (
        Index('ix_knowledge_document_project_type', 'project_id', 'document_type'),
        Index('ix_knowledge_document_source', 'source_type', 'source_record_id'),
        Index('ix_knowledge_document_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='draft')
    version: Mapped[str] = mapped_column(Text, nullable=False, default='v1')
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class KnowledgeChunk(Base):
    __tablename__ = 'knowledge_chunk'
    __table_args__ = (
        Index('ix_knowledge_chunk_document_id', 'document_id'),
        Index('ix_knowledge_chunk_project_id', 'project_id'),
        Index('ix_knowledge_chunk_content_hash', 'content_hash'),
        Index('ix_knowledge_chunk_qdrant_point_id', 'qdrant_point_id'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey('knowledge_document.id'), nullable=False)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    qdrant_point_id: Mapped[str | None] = mapped_column(Text)
    embedding_provider: Mapped[str | None] = mapped_column(Text)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RagIndexJob(Base):
    __tablename__ = 'rag_index_job'
    __table_args__ = (
        Index('ix_rag_index_job_project_id', 'project_id'),
        Index('ix_rag_index_job_document_id', 'document_id'),
        Index('ix_rag_index_job_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    document_id: Mapped[UUID] = mapped_column(ForeignKey('knowledge_document.id'), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='pending')
    chunks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RagRetrievalLog(Base):
    __tablename__ = 'rag_retrieval_log'
    __table_args__ = (
        Index('ix_rag_retrieval_log_mas_run_id', 'mas_run_id'),
        Index('ix_rag_retrieval_log_project_id', 'project_id'),
        Index('ix_rag_retrieval_log_provider_collection', 'provider', 'collection'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    results_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    collection: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReportSnapshot(Base):
    __tablename__ = 'report_snapshot'
    __table_args__ = (
        Index('ix_report_snapshot_project_created', 'project_id', 'created_at'),
        Index('ix_report_snapshot_project_type', 'project_id', 'report_type'),
        Index('ix_report_snapshot_context_hash', 'context_hash'),
        Index('ix_report_snapshot_mas_run_id', 'mas_run_id'),
        Index('ix_report_snapshot_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    report_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    context_hash: Mapped[str | None] = mapped_column(Text)
    strategy_mode: Mapped[str | None] = mapped_column(Text)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    company_domain: Mapped[str | None] = mapped_column(Text)
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(Text)
    calculation_version: Mapped[str | None] = mapped_column(Text)
    scoring_version: Mapped[str | None] = mapped_column(Text)
    prompt_version_id: Mapped[int | None] = mapped_column(ForeignKey('mas_prompt_version.id'))
    llm_provider: Mapped[str | None] = mapped_column(Text)
    llm_model: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    report_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    markdown_snapshot: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Insight(Base):
    __tablename__ = 'insight'
    __table_args__ = (
        Index('ix_insight_project_created', 'project_id', 'created_at'),
        Index('ix_insight_project_type', 'project_id', 'insight_type'),
        Index('ix_insight_mas_run_id', 'mas_run_id'),
        Index('ix_insight_report_snapshot_id', 'report_snapshot_id'),
        Index('ix_insight_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    report_snapshot_id: Mapped[UUID | None] = mapped_column(ForeignKey('report_snapshot.id'))
    evidence_item_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_evidence_item.id'))
    insight_type: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(Text)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    strategy_mode: Mapped[str | None] = mapped_column(Text)
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    status: Mapped[str] = mapped_column(Text, nullable=False, default='active')
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Recommendation(Base):
    __tablename__ = 'recommendation'
    __table_args__ = (
        Index('ix_recommendation_project_created', 'project_id', 'created_at'),
        Index('ix_recommendation_project_type', 'project_id', 'recommendation_type'),
        Index('ix_recommendation_mas_run_id', 'mas_run_id'),
        Index('ix_recommendation_report_snapshot_id', 'report_snapshot_id'),
        Index('ix_recommendation_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    report_snapshot_id: Mapped[UUID | None] = mapped_column(ForeignKey('report_snapshot.id'))
    insight_id: Mapped[UUID | None] = mapped_column(ForeignKey('insight.id'))
    recommendation_type: Mapped[str] = mapped_column(Text, nullable=False)
    strategy_mode: Mapped[str | None] = mapped_column(Text)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    channel: Mapped[str | None] = mapped_column(Text)
    budget_share: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    status: Mapped[str] = mapped_column(Text, nullable=False, default='proposed')
    user_decision: Mapped[str | None] = mapped_column(Text)
    user_decision_reason: Mapped[str | None] = mapped_column(Text)
    linked_mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    linked_evidence_item_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner: Mapped[str | None] = mapped_column(Text)
    expected_outcome_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    actual_outcome_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    feedback_status: Mapped[str] = mapped_column(Text, nullable=False, default='not_reviewed')
    linked_campaign_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True))
    learning_status: Mapped[str] = mapped_column(Text, nullable=False, default='not_started')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RecommendationDecision(Base):
    __tablename__ = 'recommendation_decision'
    __table_args__ = (
        Index('ix_recommendation_decision_project_created', 'project_id', 'created_at'),
        Index('ix_recommendation_decision_recommendation', 'recommendation_id'),
        Index('ix_recommendation_decision_decision', 'decision'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    recommendation_id: Mapped[UUID] = mapped_column(ForeignKey('recommendation.id'), nullable=False)
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    user_id: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reason_category: Mapped[str] = mapped_column(Text, nullable=False, default='unknown')
    reason_text: Mapped[str | None] = mapped_column(Text)
    expected_action_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ActionExecution(Base):
    __tablename__ = 'action_execution'
    __table_args__ = (
        Index('ix_action_execution_project_created', 'project_id', 'created_at'),
        Index('ix_action_execution_recommendation', 'recommendation_id'),
        Index('ix_action_execution_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    recommendation_id: Mapped[UUID | None] = mapped_column(ForeignKey('recommendation.id'))
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    strategy_mode: Mapped[str | None] = mapped_column(Text)
    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str | None] = mapped_column(Text)
    planned_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    actual_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='planned')
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ActionResult(Base):
    __tablename__ = 'action_result'
    __table_args__ = (
        Index('ix_action_result_project_created', 'project_id', 'created_at'),
        Index('ix_action_result_action', 'action_execution_id'),
        Index('ix_action_result_recommendation', 'recommendation_id'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    action_execution_id: Mapped[UUID] = mapped_column(ForeignKey('action_execution.id'), nullable=False)
    recommendation_id: Mapped[UUID | None] = mapped_column(ForeignKey('recommendation.id'))
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    channel: Mapped[str | None] = mapped_column(Text)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    traffic: Mapped[int | None] = mapped_column(BigInteger)
    traffic_growth: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    bounce_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    avg_visit_duration: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    pages_per_visit: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    spend: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    conversions: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cac: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    cpa: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    roi: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    payback_days: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RecommendationExpectation(Base):
    __tablename__ = 'recommendation_expectation'
    __table_args__ = (
        Index('ix_recommendation_expectation_project_created', 'project_id', 'created_at'),
        Index('ix_recommendation_expectation_recommendation', 'recommendation_id'),
        Index('ix_recommendation_expectation_metric', 'expected_metric'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    recommendation_id: Mapped[UUID] = mapped_column(ForeignKey('recommendation.id'), nullable=False)
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    expected_direction: Mapped[str] = mapped_column(Text, nullable=False)
    expected_metric: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    expected_value_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    expected_time_window_days: Mapped[int | None] = mapped_column(Integer)
    assumptions_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Assumption(Base):
    __tablename__ = 'assumption'
    __table_args__ = (
        Index('ix_assumption_project_created', 'project_id', 'created_at'),
        Index('ix_assumption_recommendation', 'recommendation_id'),
        Index('ix_assumption_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    recommendation_id: Mapped[UUID | None] = mapped_column(ForeignKey('recommendation.id'))
    mas_run_id: Mapped[UUID | None] = mapped_column(ForeignKey('mas_run.id'))
    assumption_type: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    status: Mapped[str] = mapped_column(Text, nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LearningEvent(Base):
    __tablename__ = 'learning_event'
    __table_args__ = (
        Index('ix_learning_event_project_created', 'project_id', 'created_at'),
        Index('ix_learning_event_recommendation', 'recommendation_id'),
        Index('ix_learning_event_type', 'learning_type'),
        Index('ix_learning_event_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(Text)
    recommendation_id: Mapped[UUID | None] = mapped_column(ForeignKey('recommendation.id'))
    action_execution_id: Mapped[UUID | None] = mapped_column(ForeignKey('action_execution.id'))
    learning_type: Mapped[str] = mapped_column(Text, nullable=False)
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    channel: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    impact_area: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    status: Mapped[str] = mapped_column(Text, nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScoringModelReview(Base):
    __tablename__ = 'scoring_model_review'
    __table_args__ = (
        Index('ix_scoring_model_review_project_created', 'project_id', 'created_at'),
        Index('ix_scoring_model_review_learning', 'source_learning_event_id'),
        Index('ix_scoring_model_review_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_learning_event_id: Mapped[UUID | None] = mapped_column(ForeignKey('learning_event.id'))
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    current_version: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_version: Mapped[str | None] = mapped_column(Text)
    proposed_changes_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='proposed')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DataUpdateBatch(Base):
    __tablename__ = 'data_update_batch'
    __table_args__ = (
        Index('ix_data_update_batch_project_created', 'project_id', 'created_at'),
        Index('ix_data_update_batch_project_source', 'project_id', 'source_type'),
        Index('ix_data_update_batch_status', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_file: Mapped[str | None] = mapped_column(Text)
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='pending')
    rows_loaded: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    rows_failed: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    validation_status: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class DataFreshnessStatus(Base):
    __tablename__ = 'data_freshness_status'
    __table_args__ = (
        Index('ix_data_freshness_project_dataset', 'project_id', 'dataset_type', unique=True),
        Index('ix_data_freshness_status', 'freshness_status'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    dataset_type: Mapped[str] = mapped_column(Text, nullable=False)
    latest_available_date: Mapped[date | None] = mapped_column(Date)
    latest_loaded_date: Mapped[date | None] = mapped_column(Date)
    last_update_batch_id: Mapped[UUID | None] = mapped_column(ForeignKey('data_update_batch.id'))
    freshness_status: Mapped[str] = mapped_column(Text, nullable=False, default='unknown')
    lag_days: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AnalyticsRecalculationJob(Base):
    __tablename__ = 'analytics_recalculation_job'
    __table_args__ = (
        Index('ix_analytics_recalculation_project_created', 'project_id', 'started_at'),
        Index('ix_analytics_recalculation_batch', 'data_update_batch_id'),
        Index('ix_analytics_recalculation_type_status', 'job_type', 'status'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    data_update_batch_id: Mapped[UUID | None] = mapped_column(ForeignKey('data_update_batch.id'))
    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='pending')
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    calculation_version: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class AlertRule(Base):
    __tablename__ = 'alert_rule'
    __table_args__ = (
        Index('ix_alert_rule_project_type', 'project_id', 'alert_type'),
        Index('ix_alert_rule_enabled', 'is_enabled'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    alert_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity_default: Mapped[str] = mapped_column(Text, nullable=False, default='medium')
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    threshold_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    cooldown_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    scope_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AlertEvent(Base):
    __tablename__ = 'alert_event'
    __table_args__ = (
        Index('ix_alert_event_project_created', 'project_id', 'created_at'),
        Index('ix_alert_event_project_status', 'project_id', 'status'),
        Index('ix_alert_event_project_type', 'project_id', 'alert_type'),
        Index('ix_alert_event_project_severity', 'project_id', 'severity'),
        Index('ix_alert_event_context_hash', 'context_hash'),
        Index('ix_alert_event_dedupe_key', 'dedupe_key'),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    alert_rule_id: Mapped[int | None] = mapped_column(ForeignKey('alert_rule.id'))
    alert_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default='new')
    country_id: Mapped[int | None] = mapped_column(ForeignKey('dim_country.id'))
    company_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    competitor_id: Mapped[int | None] = mapped_column(ForeignKey('dim_company.id'))
    channel: Mapped[str | None] = mapped_column(Text)
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    related_signal_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    related_score_ids: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    related_insight_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    context_hash: Mapped[str | None] = mapped_column(Text)
    dedupe_key: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FactTrafficCountriesDaily(Base):
    __tablename__ = 'fact_traffic_countries_daily'
    __table_args__ = (
        Index('ix_fact_traffic_countries_daily_date', 'date'),
        Index('ix_fact_traffic_countries_daily_company_id', 'company_id'),
        Index('ix_fact_traffic_countries_daily_domain_id', 'domain_id'),
        Index('ix_fact_traffic_countries_daily_country_id', 'country_id'),
        Index('ix_fact_traffic_countries_daily_project_id', 'project_id'),
        Index('ix_fact_traffic_countries_daily_ingestion_run_id', 'ingestion_run_id'),
        Index(
            'ix_fact_traffic_countries_project_country_company_domain_date',
            'project_id',
            'country_id',
            'company_id',
            'domain_id',
            'date',
        ),
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
        Index('ix_fact_traffic_sources_project_date', 'project_id', 'date'),
        Index('ix_fact_traffic_sources_project_company_date', 'project_id', 'company_id', 'date'),
        Index('ix_fact_traffic_sources_project_domain_date', 'project_id', 'domain_id', 'date'),
        Index(
            'ix_fact_traffic_sources_project_company_domain_date',
            'project_id',
            'company_id',
            'domain_id',
            'date',
        ),
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
        Index('ix_fact_journey_sources_project_date', 'project_id', 'date'),
        Index('ix_fact_journey_sources_project_company_date', 'project_id', 'company_id', 'date'),
        Index('ix_fact_journey_sources_project_domain_date', 'project_id', 'domain_id', 'date'),
        Index('ix_fact_journey_sources_project_source_date', 'project_id', 'source_type', 'date'),
        Index('ix_fact_journey_sources_project_traffic_date', 'project_id', 'traffic_type', 'date'),
        Index('ix_fact_journey_sources_project_search_date', 'project_id', 'search_source', 'date'),
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
        Index('ix_fact_device_trends_project_date', 'project_id', 'date'),
        Index('ix_fact_device_trends_project_company_date', 'project_id', 'company_id', 'date'),
        Index('ix_fact_device_trends_project_domain_date', 'project_id', 'domain_id', 'date'),
        Index(
            'ix_fact_device_trends_project_company_domain_date',
            'project_id',
            'company_id',
            'domain_id',
            'date',
        ),
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
