from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.alerts.schemas import (
    AlertDetectRequest,
    AlertDetectResponse,
    AlertEventRead,
    AlertListResponse,
    AlertStatusUpdate,
    AlertSummaryResponse,
    UpdateStatusResponse,
)
from app.alerts.service import (
    DataUpdateScheduler,
    alert_summary,
    list_alerts,
    read_alert,
    update_alert,
)
from app.analytics.country_intelligence import resolve_project
from app.core.config import get_settings
from app.core.database import get_session

router = APIRouter(prefix='/alerts', tags=['alerts'])
SESSION_DEPENDENCY = Depends(get_session)
ALERT_TYPE_QUERY = Query(default=None)
SEVERITY_QUERY = Query(default=None)
STATUS_QUERY = Query(default=None)
DATE_FROM_QUERY = Query(default=None)
DATE_TO_QUERY = Query(default=None)
COUNTRY_ID_QUERY = Query(default=None)
COMPANY_ID_QUERY = Query(default=None)


def project_id() -> UUID:
    """Resolve project identifier.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    return resolve_project(None, settings.default_project_id)


def build_filters(
    alert_type: str | None,
    severity: str | None,
    status: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    country_id: int | None,
    company_id: int | None,
) -> dict[str, object]:
    """Build alert filters.
    Args:
        alert_type (str | None): Optional alert type.
        severity (str | None): Optional severity.
        status (str | None): Optional status.
        date_from (datetime | None): Optional detected start.
        date_to (datetime | None): Optional detected end.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier."""
    return {
        'alert_type': alert_type,
        'severity': severity,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'country_id': country_id,
        'company_id': company_id,
    }


@router.get('', response_model=AlertListResponse)
def read_alerts(
    session: Session = SESSION_DEPENDENCY,
    alert_type: str | None = ALERT_TYPE_QUERY,
    severity: str | None = SEVERITY_QUERY,
    status: str | None = STATUS_QUERY,
    date_from: datetime | None = DATE_FROM_QUERY,
    date_to: datetime | None = DATE_TO_QUERY,
    country_id: int | None = COUNTRY_ID_QUERY,
    company_id: int | None = COMPANY_ID_QUERY,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AlertListResponse:
    """Read alerts.
    Args:
        session (Session): Active database session.
        alert_type (str | None): Optional alert type.
        severity (str | None): Optional severity.
        status (str | None): Optional status.
        date_from (datetime | None): Optional detected start.
        date_to (datetime | None): Optional detected end.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    filters = build_filters(alert_type, severity, status, date_from, date_to, country_id, company_id)
    items, total = list_alerts(session, project_id(), filters, limit, offset)
    return AlertListResponse(items=items, total=total)


@router.get('/summary', response_model=AlertSummaryResponse)
def read_summary(
    session: Session = SESSION_DEPENDENCY,
    alert_type: str | None = ALERT_TYPE_QUERY,
    severity: str | None = SEVERITY_QUERY,
    status: str | None = STATUS_QUERY,
    date_from: datetime | None = DATE_FROM_QUERY,
    date_to: datetime | None = DATE_TO_QUERY,
    country_id: int | None = COUNTRY_ID_QUERY,
    company_id: int | None = COMPANY_ID_QUERY,
) -> AlertSummaryResponse:
    """Read alerts summary.
    Args:
        session (Session): Active database session.
        alert_type (str | None): Optional alert type.
        severity (str | None): Optional severity.
        status (str | None): Optional status.
        date_from (datetime | None): Optional detected start.
        date_to (datetime | None): Optional detected end.
        country_id (int | None): Optional country identifier.
        company_id (int | None): Optional company identifier."""
    filters = build_filters(alert_type, severity, status, date_from, date_to, country_id, company_id)
    return AlertSummaryResponse(**alert_summary(session, project_id(), filters))


@router.get('/status', response_model=UpdateStatusResponse)
def read_status(session: Session = SESSION_DEPENDENCY) -> UpdateStatusResponse:
    """Read update status.
    Args:
        session (Session): Active database session."""
    scheduler = DataUpdateScheduler()
    return UpdateStatusResponse(**scheduler.get_update_status(session, project_id()))


@router.post('/detect', response_model=AlertDetectResponse)
def detect_alerts(
    request: AlertDetectRequest,
    session: Session = SESSION_DEPENDENCY,
) -> AlertDetectResponse:
    """Detect alerts.
    Args:
        request (AlertDetectRequest): Alert detection request.
        session (Session): Active database session."""
    scheduler = DataUpdateScheduler()
    result = scheduler.run_manual_update(session, project_id(), request)
    batch = result.get('data_update_batch')
    alert_result = result['alert_result']
    return AlertDetectResponse(
        status='success',
        data_update_batch_id=batch.id if batch is not None else None,
        jobs=result['jobs'],
        alerts_created=alert_result['created'],
        alerts_updated=alert_result['updated'],
        alerts=alert_result['events'],
    )


@router.get('/{alert_id}', response_model=AlertEventRead)
def read_alert_event(alert_id: UUID, session: Session = SESSION_DEPENDENCY) -> AlertEventRead:
    """Read alert event.
    Args:
        alert_id (UUID): Alert event identifier.
        session (Session): Active database session."""
    record = read_alert(session, project_id(), alert_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Alert was not found')
    return record


@router.patch('/{alert_id}/status', response_model=AlertEventRead)
def update_alert_status(
    alert_id: UUID,
    request: AlertStatusUpdate,
    session: Session = SESSION_DEPENDENCY,
) -> AlertEventRead:
    """Update alert status.
    Args:
        alert_id (UUID): Alert event identifier.
        request (AlertStatusUpdate): Status update request.
        session (Session): Active database session."""
    record = read_alert(session, project_id(), alert_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Alert was not found')
    try:
        return update_alert(session, record, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
