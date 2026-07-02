from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ReportSnapshotRead(BaseModel):
    id: UUID
    project_id: UUID
    report_type: str
    source_type: str
    source_record_id: str | None
    mas_run_id: UUID | None
    context_hash: str | None
    strategy_mode: str | None
    country_id: int | None
    company_id: int | None
    company_domain: str | None
    period_from: date | None
    period_to: date | None
    budget_amount: Decimal | None
    currency: str | None
    calculation_version: str | None
    scoring_version: str | None
    prompt_version_id: int | None
    llm_provider: str | None
    llm_model: str | None
    title: str
    summary: str
    report_json: dict[str, Any]
    markdown_snapshot: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class InsightRead(BaseModel):
    id: UUID
    project_id: UUID
    source_type: str
    source_record_id: str | None
    mas_run_id: UUID | None
    report_snapshot_id: UUID | None
    evidence_item_id: UUID | None
    insight_type: str
    category: str | None
    severity: str | None
    country_id: int | None
    company_id: int | None
    strategy_mode: str | None
    period_from: date | None
    period_to: date | None
    title: str
    summary: str
    details_json: dict[str, Any]
    confidence: str
    status: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class RecommendationRead(BaseModel):
    id: UUID
    project_id: UUID
    source_type: str
    source_record_id: str | None
    mas_run_id: UUID | None
    report_snapshot_id: UUID | None
    insight_id: UUID | None
    recommendation_type: str
    strategy_mode: str | None
    country_id: int | None
    company_id: int | None
    period_from: date | None
    period_to: date | None
    title: str
    description: str
    action: str
    priority: str
    channel: str | None
    budget_share: Decimal | None
    budget_amount: Decimal | None
    currency: str | None
    confidence: str
    status: str
    user_decision: str | None
    user_decision_reason: str | None
    linked_mas_run_id: UUID | None
    linked_evidence_item_ids: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class HistoryListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int


class ReportSnapshotListResponse(BaseModel):
    items: list[ReportSnapshotRead]
    total: int


class InsightListResponse(BaseModel):
    items: list[InsightRead]
    total: int


class RecommendationListResponse(BaseModel):
    items: list[RecommendationRead]
    total: int


class RecommendationStatusUpdate(BaseModel):
    status: str = Field(min_length=1)
    user_decision: str | None = None
    user_decision_reason: str | None = None
