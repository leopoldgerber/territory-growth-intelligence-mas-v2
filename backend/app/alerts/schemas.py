from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DataUpdateBatchRead(BaseModel):
    id: UUID
    project_id: UUID
    source_type: str
    source_file: str | None
    period_from: date | None
    period_to: date | None
    status: str
    rows_loaded: int
    rows_failed: int
    validation_status: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    error_message: str | None
    metadata_json: dict[str, Any]

    model_config = {'from_attributes': True}


class DataFreshnessRead(BaseModel):
    id: int
    project_id: UUID
    dataset_type: str
    latest_available_date: date | None
    latest_loaded_date: date | None
    last_update_batch_id: UUID | None
    freshness_status: str
    lag_days: int | None
    updated_at: datetime

    model_config = {'from_attributes': True}


class RecalculationJobRead(BaseModel):
    id: UUID
    project_id: UUID
    data_update_batch_id: UUID | None
    job_type: str
    status: str
    period_from: date | None
    period_to: date | None
    calculation_version: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    metrics_json: dict[str, Any]

    model_config = {'from_attributes': True}


class AlertRuleRead(BaseModel):
    id: int
    project_id: UUID
    alert_type: str
    name: str
    description: str
    severity_default: str
    is_enabled: bool
    threshold_json: dict[str, Any]
    cooldown_hours: int
    scope_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class AlertEventRead(BaseModel):
    id: UUID
    project_id: UUID
    alert_rule_id: int | None
    alert_type: str
    severity: str
    status: str
    country_id: int | None
    company_id: int | None
    competitor_id: int | None
    channel: str | None
    period_from: date | None
    period_to: date | None
    title: str
    summary: str
    details_json: dict[str, Any]
    evidence_refs_json: list[dict[str, Any]]
    related_signal_ids: list[int]
    related_score_ids: list[int]
    related_insight_ids: list[str]
    context_hash: str | None
    dedupe_key: str
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    model_config = {'from_attributes': True}


class AlertListResponse(BaseModel):
    items: list[AlertEventRead]
    total: int


class AlertSummaryResponse(BaseModel):
    total: int
    new_alerts: int
    high_severity: int
    market_windows: int
    competitor_movements: int
    quality_risks: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    by_type: dict[str, int]


class AlertDetectRequest(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    calculation_version: str = 'v1'
    run_recalculation: bool = True


class AlertDetectResponse(BaseModel):
    status: str
    data_update_batch_id: UUID | None
    jobs: list[RecalculationJobRead]
    alerts_created: int
    alerts_updated: int
    alerts: list[AlertEventRead]


class AlertStatusUpdate(BaseModel):
    status: str = Field(min_length=1)


class UpdateStatusResponse(BaseModel):
    freshness: list[DataFreshnessRead]
    latest_batches: list[DataUpdateBatchRead]
    latest_jobs: list[RecalculationJobRead]
