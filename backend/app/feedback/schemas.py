from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationDecisionCreate(BaseModel):
    user_id: str | None = None
    decision: str = Field(min_length=1)
    reason_category: str = 'unknown'
    reason_text: str | None = None
    expected_action_json: dict[str, Any] = Field(default_factory=dict)


class RecommendationDecisionRead(BaseModel):
    id: UUID
    project_id: UUID
    recommendation_id: UUID
    mas_run_id: UUID | None
    user_id: str | None
    decision: str
    reason_category: str
    reason_text: str | None
    expected_action_json: dict[str, Any]
    created_at: datetime

    model_config = {'from_attributes': True}


class ActionExecutionCreate(BaseModel):
    recommendation_id: UUID | None = None
    country_id: int | None = None
    company_id: int | None = None
    strategy_mode: str | None = None
    action_type: str = Field(min_length=1)
    channel: str | None = None
    planned_budget: Decimal | None = None
    actual_budget: Decimal | None = None
    currency: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = 'planned'
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ActionExecutionUpdate(BaseModel):
    status: str | None = None
    actual_budget: Decimal | None = None
    end_date: date | None = None
    metadata_json: dict[str, Any] | None = None


class ActionExecutionRead(BaseModel):
    id: UUID
    project_id: UUID
    recommendation_id: UUID | None
    country_id: int | None
    company_id: int | None
    strategy_mode: str | None
    action_type: str
    channel: str | None
    planned_budget: Decimal | None
    actual_budget: Decimal | None
    currency: str | None
    start_date: date | None
    end_date: date | None
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class ActionResultCreate(BaseModel):
    period_from: date | None = None
    period_to: date | None = None
    channel: str | None = None
    country_id: int | None = None
    company_id: int | None = None
    traffic: int | None = None
    traffic_growth: Decimal | None = None
    bounce_rate: Decimal | None = None
    avg_visit_duration: Decimal | None = None
    pages_per_visit: Decimal | None = None
    spend: Decimal | None = None
    conversions: Decimal | None = None
    revenue: Decimal | None = None
    cac: Decimal | None = None
    cpa: Decimal | None = None
    roi: Decimal | None = None
    payback_days: int | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ActionResultRead(BaseModel):
    id: UUID
    project_id: UUID
    action_execution_id: UUID
    recommendation_id: UUID | None
    period_from: date | None
    period_to: date | None
    channel: str | None
    country_id: int | None
    company_id: int | None
    traffic: int | None
    traffic_growth: Decimal | None
    bounce_rate: Decimal | None
    avg_visit_duration: Decimal | None
    pages_per_visit: Decimal | None
    spend: Decimal | None
    conversions: Decimal | None
    revenue: Decimal | None
    cac: Decimal | None
    cpa: Decimal | None
    roi: Decimal | None
    payback_days: int | None
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {'from_attributes': True}


class RecommendationExpectationCreate(BaseModel):
    expected_direction: str = 'directional'
    expected_metric: str = 'traffic_outcome'
    expected_value_min: Decimal | None = None
    expected_value_max: Decimal | None = None
    expected_time_window_days: int | None = None
    assumptions_json: dict[str, Any] = Field(default_factory=dict)
    confidence: str = 'medium'


class RecommendationExpectationRead(BaseModel):
    id: UUID
    project_id: UUID
    recommendation_id: UUID
    mas_run_id: UUID | None
    expected_direction: str
    expected_metric: str
    expected_value_min: Decimal | None
    expected_value_max: Decimal | None
    expected_time_window_days: int | None
    assumptions_json: dict[str, Any]
    confidence: str
    created_at: datetime

    model_config = {'from_attributes': True}


class AssumptionRead(BaseModel):
    id: UUID
    project_id: UUID
    source_type: str
    source_record_id: str | None
    recommendation_id: UUID | None
    mas_run_id: UUID | None
    assumption_type: str
    statement: str
    evidence_refs_json: list[dict[str, Any]]
    confidence: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class LearningEventRead(BaseModel):
    id: UUID
    project_id: UUID
    source_type: str
    source_record_id: str | None
    recommendation_id: UUID | None
    action_execution_id: UUID | None
    learning_type: str
    country_id: int | None
    company_id: int | None
    channel: str | None
    summary: str
    details_json: dict[str, Any]
    impact_area: str
    confidence: str
    status: str
    created_at: datetime

    model_config = {'from_attributes': True}


class ScoringModelReviewRead(BaseModel):
    id: UUID
    project_id: UUID
    source_learning_event_id: UUID | None
    model_name: str
    current_version: str
    proposed_version: str | None
    proposed_changes_json: dict[str, Any]
    reason: str
    status: str
    created_at: datetime
    reviewed_at: datetime | None
    applied_at: datetime | None

    model_config = {'from_attributes': True}


class OutcomeComparisonRead(BaseModel):
    recommendation_id: UUID
    classification: str
    outcome_score: float
    learning_event: LearningEventRead
    notes: list[str]
    assumptions_updated: int
    model_review: ScoringModelReviewRead | None


class FeedbackListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int


class ActionExecutionListResponse(BaseModel):
    items: list[ActionExecutionRead]
    total: int


class LearningEventListResponse(BaseModel):
    items: list[LearningEventRead]
    total: int


class ModelReviewListResponse(BaseModel):
    items: list[ScoringModelReviewRead]
    total: int
