from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_session
from app.reports.budget_strategy.schemas import (
    BudgetStrategyGenerateRequest,
    BudgetStrategyListResponse,
    BudgetStrategyReportResponse,
)
from app.reports.budget_strategy.service import generate_strategy, get_strategy, list_strategies

router = APIRouter(prefix='/reports', tags=['reports'])
SESSION_DEPENDENCY = Depends(get_session)
DATE_FROM_QUERY = Query(default=None, alias='dateFrom')
DATE_TO_QUERY = Query(default=None, alias='dateTo')


@router.post('/budget-strategy/generate', response_model=BudgetStrategyReportResponse)
def generate_budget_strategy(
    request: BudgetStrategyGenerateRequest,
    session: Session = SESSION_DEPENDENCY,
) -> BudgetStrategyReportResponse:
    """Generate a budget strategy report.
    Args:
        request (BudgetStrategyGenerateRequest): Strategy generation request.
        session (Session): Active database session."""
    settings = get_settings()
    try:
        return generate_strategy(session, settings.default_project_id, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get('/budget-strategy', response_model=BudgetStrategyListResponse)
def read_budget_strategies(
    session: Session = SESSION_DEPENDENCY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    country: str | None = Query(default=None),
    scope: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> BudgetStrategyListResponse:
    """Read saved budget strategy reports.
    Args:
        session (Session): Active database session.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country.
        scope (str | None): Requested scope.
        limit (int): Result limit."""
    settings = get_settings()
    return list_strategies(session, settings.default_project_id, date_from, date_to, country, scope, limit)


@router.get('/budget-strategy/{report_id}', response_model=BudgetStrategyReportResponse)
def read_budget_strategy(
    report_id: int,
    session: Session = SESSION_DEPENDENCY,
) -> BudgetStrategyReportResponse:
    """Read one saved budget strategy report.
    Args:
        report_id (int): Report identifier.
        session (Session): Active database session."""
    settings = get_settings()
    response = get_strategy(session, settings.default_project_id, report_id)
    if response is None:
        raise HTTPException(status_code=404, detail='Budget strategy report was not found')
    return response
