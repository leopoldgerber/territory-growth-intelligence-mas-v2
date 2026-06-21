from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import get_channel_intelligence
from app.analytics.competitor_intelligence import get_competitor_intelligence
from app.analytics.country_intelligence import fetch_filter_options, get_country_intelligence
from app.analytics.device_intelligence import get_device_intelligence
from app.analytics.scoring.service import list_scores, recalculate_scores, summarize_scores
from app.analytics.signals.service import get_signal_summary, list_derived_signals, recalculate_signals
from app.core.config import get_settings
from app.core.database import get_session
from app.schemas.analytics import (
    AnalyticsFilterOptionsResponse,
    ChannelIntelligenceResponse,
    CompetitorIntelligenceResponse,
    CountryIntelligenceResponse,
    DerivedSignalResponse,
    DerivedSignalSummary,
    DeviceIntelligenceResponse,
    OpportunityScoreRecalculateRequest,
    OpportunityScoreRecalculateResponse,
    OpportunityScoresResponse,
    OpportunityScoreSummary,
    RecalculateSignalsRequest,
    RecalculateSignalsResponse,
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
SIGNAL_GROUP_QUERY = Query(default='all', alias='signalGroup')
SIGNAL_TYPE_QUERY = Query(default='all', alias='signalType')
ENTITY_TYPE_QUERY = Query(default='all', alias='entityType')
SEVERITY_QUERY = Query(default='all')
SCOPE_QUERY = Query(default='all')
SCORE_CATEGORY_QUERY = Query(default='all', alias='scoreCategory')
DOMAIN_QUERY = Query(default='all')


@router.post('/scoring/recalculate', response_model=OpportunityScoreRecalculateResponse)
def recalculate_opportunity_scores(
    request: OpportunityScoreRecalculateRequest,
    session: Session = SESSION_DEPENDENCY,
) -> OpportunityScoreRecalculateResponse:
    """Recalculate opportunity scores.
    Args:
        request (OpportunityScoreRecalculateRequest): Opportunity scoring request.
        session (Session): Active database session."""
    settings = get_settings()
    try:
        return recalculate_scores(session, settings.default_project_id, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get('/scoring/opportunities', response_model=OpportunityScoresResponse)
def read_opportunity_scores(
    session: Session = SESSION_DEPENDENCY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    country: str = COUNTRY_QUERY,
    scope: str = SCOPE_QUERY,
    score_category: str = SCORE_CATEGORY_QUERY,
    limit: int = LIMIT_QUERY,
) -> OpportunityScoresResponse:
    """Read persisted opportunity scores.
    Args:
        session (Session): Active database session.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str): Requested country values.
        scope (str): Requested analytical scopes.
        score_category (str): Requested score categories.
        limit (int): Requested result limit."""
    settings = get_settings()
    return list_scores(
        session,
        settings.default_project_id,
        date_from,
        date_to,
        country,
        scope,
        score_category,
        limit,
    )


@router.get('/scoring/summary', response_model=OpportunityScoreSummary)
def read_opportunity_summary(
    session: Session = SESSION_DEPENDENCY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    country: str = COUNTRY_QUERY,
    scope: str = SCOPE_QUERY,
    score_category: str = SCORE_CATEGORY_QUERY,
) -> OpportunityScoreSummary:
    """Read opportunity scoring summary.
    Args:
        session (Session): Active database session.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str): Requested country values.
        scope (str): Requested analytical scopes.
        score_category (str): Requested score categories."""
    settings = get_settings()
    response = list_scores(
        session,
        settings.default_project_id,
        date_from,
        date_to,
        country,
        scope,
        score_category,
        100,
    )
    return summarize_scores(response.items)


@router.post('/signals/recalculate', response_model=RecalculateSignalsResponse)
def recalculate_derived_signals(
    request: RecalculateSignalsRequest,
    session: Session = SESSION_DEPENDENCY,
) -> RecalculateSignalsResponse:
    """Recalculate derived analytics signals.
    Args:
        request (RecalculateSignalsRequest): Signal recalculation request.
        session (Session): Active database session."""
    settings = get_settings()
    try:
        response = recalculate_signals(session, settings.default_project_id, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return response


@router.get('/signals', response_model=list[DerivedSignalResponse])
def read_derived_signals(
    session: Session = SESSION_DEPENDENCY,
    project_id: str | None = PROJECT_ID_QUERY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    signal_group: str = SIGNAL_GROUP_QUERY,
    signal_type: str = SIGNAL_TYPE_QUERY,
    entity_type: str = ENTITY_TYPE_QUERY,
    country: str = COUNTRY_QUERY,
    company: str = COMPANY_QUERY,
    domain: str = DOMAIN_QUERY,
    severity: str = SEVERITY_QUERY,
    scope: str = SCOPE_QUERY,
    limit: int = LIMIT_QUERY,
) -> list[DerivedSignalResponse]:
    """Read persisted derived signals.
    Args:
        session (Session): Active database session.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested calculation start date.
        date_to (date | None): Requested calculation end date.
        signal_group (str): Requested signal groups.
        signal_type (str): Requested signal types.
        entity_type (str): Requested entity types.
        country (str): Requested country values.
        company (str): Requested company identifiers.
        domain (str): Requested domain values.
        severity (str): Requested severity values.
        scope (str): Requested analytical scope.
        limit (int): Requested result limit."""
    settings = get_settings()
    return list_derived_signals(
        session,
        settings.default_project_id,
        project_id,
        date_from,
        date_to,
        signal_group,
        signal_type,
        entity_type,
        country,
        company,
        domain,
        severity,
        scope,
        limit,
    )


@router.get('/signals/summary', response_model=DerivedSignalSummary)
def read_signal_summary(
    session: Session = SESSION_DEPENDENCY,
    project_id: str | None = PROJECT_ID_QUERY,
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    signal_group: str = SIGNAL_GROUP_QUERY,
    signal_type: str = SIGNAL_TYPE_QUERY,
    entity_type: str = ENTITY_TYPE_QUERY,
    country: str = COUNTRY_QUERY,
    company: str = COMPANY_QUERY,
    domain: str = DOMAIN_QUERY,
    severity: str = SEVERITY_QUERY,
    scope: str = SCOPE_QUERY,
) -> DerivedSignalSummary:
    """Read derived signal summary.
    Args:
        session (Session): Active database session.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested calculation start date.
        date_to (date | None): Requested calculation end date.
        signal_group (str): Requested signal groups.
        signal_type (str): Requested signal types.
        entity_type (str): Requested entity types.
        country (str): Requested country values.
        company (str): Requested company identifiers.
        domain (str): Requested domain values.
        severity (str): Requested severity values.
        scope (str): Requested analytical scope."""
    settings = get_settings()
    return get_signal_summary(
        session,
        settings.default_project_id,
        project_id,
        date_from,
        date_to,
        signal_group,
        signal_type,
        entity_type,
        country,
        company,
        domain,
        severity,
        scope,
    )


@router.get('/device-intelligence', response_model=DeviceIntelligenceResponse)
def read_device_intelligence(
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
) -> DeviceIntelligenceResponse:
    """Read device intelligence analytics.
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
        competitor_domain (str): Requested competitor domains.
        limit (int): Requested result limit."""
    settings = get_settings()
    response = get_device_intelligence(
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


@router.get('/channel-intelligence', response_model=ChannelIntelligenceResponse)
def read_channel_intelligence(
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
) -> ChannelIntelligenceResponse:
    """Read channel intelligence analytics.
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
        competitor_domain (str): Requested competitor domains.
        limit (int): Requested result limit."""
    settings = get_settings()
    response = get_channel_intelligence(
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
