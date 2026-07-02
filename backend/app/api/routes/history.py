from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import resolve_project
from app.api.routes.mas import build_detail, build_summary
from app.core.config import get_settings
from app.core.database import get_session
from app.history.schemas import (
    InsightListResponse,
    InsightRead,
    RecommendationListResponse,
    RecommendationRead,
    RecommendationStatusUpdate,
    ReportSnapshotListResponse,
    ReportSnapshotRead,
)
from app.history.service import (
    list_insights,
    list_recommendations,
    list_reports,
    read_insight,
    read_recommendation,
    read_report,
    update_recommendation,
)
from app.mas.orchestrator import list_workflows
from app.mas.schemas import MasRunDetailResponse, MasRunListResponse
from app.mas.service import read_run

router = APIRouter(prefix='/history', tags=['history'])
SESSION_DEPENDENCY = Depends(get_session)
DATE_FROM_QUERY = Query(default=None)
DATE_TO_QUERY = Query(default=None)
CREATED_FROM_QUERY = Query(default=None)
CREATED_TO_QUERY = Query(default=None)
SEARCH_QUERY = Query(default=None)
MAS_RUN_ID_QUERY = Query(default=None)
COUNTRY_ID_QUERY = Query(default=None)
COMPANY_ID_QUERY = Query(default=None)


def project_id() -> UUID:
    """Resolve default project identifier.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    return resolve_project(None, settings.default_project_id)


def build_filters(
    strategy_mode: str | None,
    status: str | None,
    period_from: date | None,
    period_to: date | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    mas_run_id: UUID | None,
    country_id: int | None,
    company_id: int | None,
) -> dict[str, Any]:
    """Build history filters.
    Args:
        strategy_mode (str | None): Optional strategy mode.
        status (str | None): Optional status.
        period_from (date | None): Optional period start.
        period_to (date | None): Optional period end.
        created_from (datetime | None): Optional created start.
        created_to (datetime | None): Optional created end.
        search (str | None): Optional search text.
        mas_run_id (UUID | None): Optional MAS run identifier.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier."""
    return {
        'strategy_mode': strategy_mode,
        'status': status,
        'period_from': period_from,
        'period_to': period_to,
        'created_from': created_from,
        'created_to': created_to,
        'search': search,
        'mas_run_id': mas_run_id,
        'country_id': country_id,
        'company_id': company_id,
    }


@router.get('/mas-runs', response_model=MasRunListResponse)
def read_history_runs(
    session: Session = SESSION_DEPENDENCY,
    status: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    strategy_mode: str | None = Query(default=None),
    country: str | None = Query(default=None),
    company: str | None = Query(default=None),
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> MasRunListResponse:
    """Read historical MAS runs.
    Args:
        session (Session): Active database session.
        status (str | None): Optional run status.
        intent (str | None): Optional resolved intent.
        strategy_mode (str | None): Optional strategy mode.
        country (str | None): Optional country text.
        company (str | None): Optional company text.
        date_from (date | None): Optional created date start.
        date_to (date | None): Optional created date end.
        limit (int): Result limit.
        offset (int): Result offset."""
    items, total = list_workflows(
        session,
        project_id(),
        status,
        intent,
        strategy_mode,
        country,
        company,
        date_from,
        date_to,
        limit,
        offset,
    )
    return MasRunListResponse(items=[build_summary(item) for item in items], total=total)


@router.get('/mas-runs/{run_id}', response_model=MasRunDetailResponse)
def read_history_run(run_id: UUID, session: Session = SESSION_DEPENDENCY) -> MasRunDetailResponse:
    """Read historical MAS run.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    record = read_run(session, project_id(), run_id)
    if record is None:
        raise HTTPException(status_code=404, detail='MAS run was not found')
    return build_detail(session, record)


@router.get('/reports', response_model=ReportSnapshotListResponse)
def read_history_reports(
    session: Session = SESSION_DEPENDENCY,
    report_type: str | None = Query(default=None),
    strategy_mode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    period_from: date | None = DATE_FROM_QUERY,
    period_to: date | None = DATE_TO_QUERY,
    created_from: datetime | None = CREATED_FROM_QUERY,
    created_to: datetime | None = CREATED_TO_QUERY,
    search: str | None = SEARCH_QUERY,
    mas_run_id: UUID | None = MAS_RUN_ID_QUERY,
    country_id: int | None = COUNTRY_ID_QUERY,
    company_id: int | None = COMPANY_ID_QUERY,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ReportSnapshotListResponse:
    """Read report snapshots.
    Args:
        session (Session): Active database session.
        report_type (str | None): Optional report type.
        strategy_mode (str | None): Optional strategy mode.
        status (str | None): Optional report status.
        period_from (date | None): Optional period start.
        period_to (date | None): Optional period end.
        created_from (datetime | None): Optional created start.
        created_to (datetime | None): Optional created end.
        search (str | None): Optional search text.
        mas_run_id (UUID | None): Optional MAS run identifier.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    filters = build_filters(
        strategy_mode,
        status,
        period_from,
        period_to,
        created_from,
        created_to,
        search,
        mas_run_id,
        country_id,
        company_id,
    )
    filters['report_type'] = report_type
    items, total = list_reports(session, project_id(), filters, limit, offset)
    return ReportSnapshotListResponse(items=items, total=total)


@router.get('/reports/{report_id}', response_model=ReportSnapshotRead)
def read_history_report(report_id: UUID, session: Session = SESSION_DEPENDENCY) -> ReportSnapshotRead:
    """Read report snapshot.
    Args:
        report_id (UUID): Report snapshot identifier.
        session (Session): Active database session."""
    record = read_report(session, project_id(), report_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Report snapshot was not found')
    return record


@router.get('/insights', response_model=InsightListResponse)
def read_history_insights(
    session: Session = SESSION_DEPENDENCY,
    insight_type: str | None = Query(default=None),
    strategy_mode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    confidence: str | None = Query(default=None),
    period_from: date | None = DATE_FROM_QUERY,
    period_to: date | None = DATE_TO_QUERY,
    created_from: datetime | None = CREATED_FROM_QUERY,
    created_to: datetime | None = CREATED_TO_QUERY,
    search: str | None = SEARCH_QUERY,
    mas_run_id: UUID | None = MAS_RUN_ID_QUERY,
    country_id: int | None = COUNTRY_ID_QUERY,
    company_id: int | None = COMPANY_ID_QUERY,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> InsightListResponse:
    """Read insights.
    Args:
        session (Session): Active database session.
        insight_type (str | None): Optional insight type.
        strategy_mode (str | None): Optional strategy mode.
        status (str | None): Optional insight status.
        severity (str | None): Optional severity.
        confidence (str | None): Optional confidence.
        period_from (date | None): Optional period start.
        period_to (date | None): Optional period end.
        created_from (datetime | None): Optional created start.
        created_to (datetime | None): Optional created end.
        search (str | None): Optional search text.
        mas_run_id (UUID | None): Optional MAS run identifier.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    filters = build_filters(
        strategy_mode,
        status,
        period_from,
        period_to,
        created_from,
        created_to,
        search,
        mas_run_id,
        country_id,
        company_id,
    )
    filters['insight_type'] = insight_type
    filters['severity'] = severity
    filters['confidence'] = confidence
    items, total = list_insights(session, project_id(), filters, limit, offset)
    return InsightListResponse(items=items, total=total)


@router.get('/insights/{insight_id}', response_model=InsightRead)
def read_history_insight(insight_id: UUID, session: Session = SESSION_DEPENDENCY) -> InsightRead:
    """Read insight.
    Args:
        insight_id (UUID): Insight identifier.
        session (Session): Active database session."""
    record = read_insight(session, project_id(), insight_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Insight was not found')
    return record


@router.get('/recommendations', response_model=RecommendationListResponse)
def read_history_recommendations(
    session: Session = SESSION_DEPENDENCY,
    recommendation_type: str | None = Query(default=None),
    strategy_mode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    confidence: str | None = Query(default=None),
    period_from: date | None = DATE_FROM_QUERY,
    period_to: date | None = DATE_TO_QUERY,
    created_from: datetime | None = CREATED_FROM_QUERY,
    created_to: datetime | None = CREATED_TO_QUERY,
    search: str | None = SEARCH_QUERY,
    mas_run_id: UUID | None = MAS_RUN_ID_QUERY,
    country_id: int | None = COUNTRY_ID_QUERY,
    company_id: int | None = COMPANY_ID_QUERY,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> RecommendationListResponse:
    """Read recommendations.
    Args:
        session (Session): Active database session.
        recommendation_type (str | None): Optional recommendation type.
        strategy_mode (str | None): Optional strategy mode.
        status (str | None): Optional recommendation status.
        confidence (str | None): Optional confidence.
        period_from (date | None): Optional period start.
        period_to (date | None): Optional period end.
        created_from (datetime | None): Optional created start.
        created_to (datetime | None): Optional created end.
        search (str | None): Optional search text.
        mas_run_id (UUID | None): Optional MAS run identifier.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    filters = build_filters(
        strategy_mode,
        status,
        period_from,
        period_to,
        created_from,
        created_to,
        search,
        mas_run_id,
        country_id,
        company_id,
    )
    filters['recommendation_type'] = recommendation_type
    filters['confidence'] = confidence
    items, total = list_recommendations(session, project_id(), filters, limit, offset)
    return RecommendationListResponse(items=items, total=total)


@router.get('/recommendations/{recommendation_id}', response_model=RecommendationRead)
def read_history_recommendation(
    recommendation_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> RecommendationRead:
    """Read recommendation.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        session (Session): Active database session."""
    record = read_recommendation(session, project_id(), recommendation_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Recommendation was not found')
    return record


@router.patch('/recommendations/{recommendation_id}/status', response_model=RecommendationRead)
def update_history_recommendation(
    recommendation_id: UUID,
    request: RecommendationStatusUpdate,
    session: Session = SESSION_DEPENDENCY,
) -> RecommendationRead:
    """Update recommendation status.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        request (RecommendationStatusUpdate): Status update payload.
        session (Session): Active database session."""
    record = read_recommendation(session, project_id(), recommendation_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Recommendation was not found')
    try:
        return update_recommendation(session, record, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
