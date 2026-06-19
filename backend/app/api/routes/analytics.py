from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.competitor_intelligence import get_competitor_intelligence
from app.analytics.country_intelligence import fetch_filter_options, get_country_intelligence
from app.core.config import get_settings
from app.core.database import get_session
from app.schemas.analytics import (
    AnalyticsFilterOptionsResponse,
    CompetitorIntelligenceResponse,
    CountryIntelligenceResponse,
)

router = APIRouter(prefix='/analytics', tags=['analytics'])
SESSION_DEPENDENCY = Depends(get_session)
PROJECT_ID_QUERY = Query(default=None, alias='projectId')
DATE_FROM_QUERY = Query(default=None, alias='dateFrom')
DATE_TO_QUERY = Query(default=None, alias='dateTo')
COUNTRY_QUERY = Query(default='all')
TLD_QUERY = Query(default='all')
COMPANY_QUERY = Query(default='all')
COMPANY_DOMAIN_QUERY = Query(default='all', alias='companyDomain')
COMPETITORS_QUERY = Query(default='all')
COMPETITOR_DOMAIN_QUERY = Query(default='all', alias='competitorDomain')
LIMIT_QUERY = Query(default=10, ge=1, le=100)


@router.get('/competitor-intelligence', response_model=CompetitorIntelligenceResponse)
def read_competitor_intelligence(
    session: Session = SESSION_DEPENDENCY,
    project_id: str | None = PROJECT_ID_QUERY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    country: str = COUNTRY_QUERY,
    tld: str = TLD_QUERY,
    competitors: str = COMPETITORS_QUERY,
    competitor_domain: str = COMPETITOR_DOMAIN_QUERY,
    limit: int = LIMIT_QUERY,
) -> CompetitorIntelligenceResponse:
    """Read competitor intelligence analytics.
    Args:
        session (Session): Active database session.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str): Requested country values.
        tld (str): Requested top-level domains.
        competitors (str): Requested competitor identifiers.
        competitor_domain (str): Requested competitor domains.
        limit (int): Requested country list limit."""
    settings = get_settings()
    response = get_competitor_intelligence(
        session=session,
        default_project_id=settings.default_project_id,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
        country=country,
        tld=tld,
        competitors=competitors,
        competitor_domain=competitor_domain,
        limit=limit,
    )
    return response


@router.get('/country-intelligence', response_model=CountryIntelligenceResponse)
def read_country_intelligence(
    session: Session = SESSION_DEPENDENCY,
    project_id: str | None = PROJECT_ID_QUERY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    country: str = COUNTRY_QUERY,
    tld: str = TLD_QUERY,
    company: str = COMPANY_QUERY,
    company_domain: str = COMPANY_DOMAIN_QUERY,
    competitors: str = COMPETITORS_QUERY,
    competitor_domain: str = COMPETITOR_DOMAIN_QUERY,
    limit: int = LIMIT_QUERY,
) -> CountryIntelligenceResponse:
    """Read country intelligence analytics.
    Args:
        session (Session): Active database session.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str): Requested country filter.
        tld (str): Requested top-level domains.
        company (str): Requested company identifiers.
        company_domain (str): Requested company domains.
        competitors (str): Requested competitor identifiers.
        competitor_domain (str): Requested competitor domains.
        limit (int): Requested top rows limit."""
    settings = get_settings()
    response = get_country_intelligence(
        session=session,
        default_project_id=settings.default_project_id,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
        country=country,
        tld=tld,
        company=company,
        company_domain=company_domain,
        competitors=competitors,
        competitor_domain=competitor_domain,
        limit=limit,
    )
    return response


@router.get('/filter-options', response_model=AnalyticsFilterOptionsResponse)
def read_filter_options(
    session: Session = SESSION_DEPENDENCY,
    project_id: str | None = PROJECT_ID_QUERY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    country: str = COUNTRY_QUERY,
    tld: str = TLD_QUERY,
    company: str = COMPANY_QUERY,
    company_domain: str = COMPANY_DOMAIN_QUERY,
    competitors: str = COMPETITORS_QUERY,
    competitor_domain: str = COMPETITOR_DOMAIN_QUERY,
) -> AnalyticsFilterOptionsResponse:
    """Read dashboard filter options.
    Args:
        session (Session): Active database session.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str): Requested country values.
        tld (str): Requested top-level domains.
        company (str): Requested company identifiers.
        company_domain (str): Requested company domains.
        competitors (str): Requested competitor identifiers.
        competitor_domain (str): Requested competitor domains."""
    settings = get_settings()
    response = fetch_filter_options(
        session=session,
        default_project_id=settings.default_project_id,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
        country=country,
        tld=tld,
        company=company,
        company_domain=company_domain,
        competitors=competitors,
        competitor_domain=competitor_domain,
    )
    return response
