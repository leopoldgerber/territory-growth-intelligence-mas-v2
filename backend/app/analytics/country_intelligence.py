from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import case, desc, false, func, or_, select, union_all
from sqlalchemy.orm import Session

from app.models.tables import DimCompany, DimCountry, DimDomain, FactTrafficCountriesDaily
from app.schemas.analytics import (
    AnalyticsFilterOptionsResponse,
    BounceSummary,
    CountryIntelligenceFilters,
    CountryIntelligenceResponse,
    CountryIntelligenceSummary,
    DeviceSplit,
    DomainFilterOption,
    EngagementMetrics,
    FilterOption,
    MarketSignal,
    TopCompetitor,
    TrafficTrendPoint,
)


def safe_int(value: Any) -> int:
    """Convert value to integer.
    Args:
        value (Any): Source value."""
    if value is None:
        return 0
    return int(value)


def safe_float(value: Any) -> float:
    """Convert value to float.
    Args:
        value (Any): Source value."""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def divide_values(numerator: int | float, denominator: int | float) -> float:
    """Divide numeric values.
    Args:
        numerator (int | float): Numerator value.
        denominator (int | float): Denominator value."""
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def normalize_text(value: str | None, default_value: str) -> str:
    """Normalize filter text.
    Args:
        value (str | None): Source filter value.
        default_value (str): Default filter value."""
    if value is None:
        return default_value
    normalized_value = value.strip()
    if not normalized_value:
        return default_value
    return normalized_value


def normalize_limit(limit: int | None) -> int:
    """Normalize top rows limit.
    Args:
        limit (int | None): Requested limit."""
    if limit is None:
        return 10
    if limit < 1:
        return 1
    if limit > 100:
        return 100
    return limit


def normalize_values(value: str | None) -> list[str] | None:
    """Normalize multi-value filter.
    Args:
        value (str | None): Comma-separated filter value."""
    normalized_value = normalize_text(value, 'all')
    if normalized_value.lower() == 'all':
        return None
    if normalized_value.lower() == 'none':
        return []
    values = [item.strip() for item in normalized_value.split(',') if item.strip()]
    return list(dict.fromkeys(values))


def normalize_ids(value: str | None) -> list[int] | None:
    """Normalize identifier filter.
    Args:
        value (str | None): Comma-separated identifier value."""
    values = normalize_values(value)
    if values is None:
        return None
    identifiers = [int(item) for item in values if item.isdigit()]
    return identifiers


def resolve_project(project_id: str | None, default_project_id: str) -> UUID:
    """Resolve project identifier.
    Args:
        project_id (str | None): Requested project identifier.
        default_project_id (str): Default project identifier."""
    normalized_project_id = normalize_text(project_id, default_project_id)
    if normalized_project_id == 'default':
        normalized_project_id = default_project_id
    return UUID(normalized_project_id)


def read_dates(
    session: Session,
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
) -> tuple[date | None, date | None]:
    """Read effective date range.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date."""
    result = session.execute(
        select(
            func.min(FactTrafficCountriesDaily.date).label('date_from'),
            func.max(FactTrafficCountriesDaily.date).label('date_to'),
        ).where(FactTrafficCountriesDaily.project_id == project_id)
    ).one()
    effective_date_from = date_from if date_from is not None else result.date_from
    effective_date_to = date_to if date_to is not None else result.date_to
    return effective_date_from, effective_date_to


def build_filters(
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
    countries: list[str] | None,
    company_ids: list[int] | None,
    domains: list[str] | None,
    tlds: list[str] | None,
) -> list[Any]:
    """Build SQLAlchemy filters.
    Args:
        project_id (UUID): Project identifier.
        date_from (date | None): Effective start date.
        date_to (date | None): Effective end date.
        countries (list[str] | None): Country filter values.
        company_ids (list[int] | None): Company identifiers.
        domains (list[str] | None): Domain filter values.
        tlds (list[str] | None): Top-level domain values."""
    filters: list[Any] = [FactTrafficCountriesDaily.project_id == project_id]

    if date_from is not None:
        filters.append(FactTrafficCountriesDaily.date >= date_from)
    if date_to is not None:
        filters.append(FactTrafficCountriesDaily.date <= date_to)
    if countries is not None:
        if not countries:
            filters.append(false())
        country_values = [country.lower() for country in countries]
        country_ids = select(DimCountry.id).where(
            or_(
                func.lower(DimCountry.iso2).in_(country_values),
                func.lower(DimCountry.iso3).in_(country_values),
                func.lower(DimCountry.country_name_en).in_(country_values),
            )
        )
        filters.append(FactTrafficCountriesDaily.country_id.in_(country_ids))
    if company_ids is not None:
        filters.append(FactTrafficCountriesDaily.company_id.in_(company_ids) if company_ids else false())
    if domains is not None:
        if not domains:
            filters.append(false())
        domain_values = [domain.lower() for domain in domains]
        domain_ids = select(DimDomain.id).where(func.lower(DimDomain.domain).in_(domain_values))
        filters.append(FactTrafficCountriesDaily.domain_id.in_(domain_ids))
    if tlds is not None:
        if not tlds:
            filters.append(false())
        tld_values = [tld.lower().lstrip('.') for tld in tlds]
        tld_domain_ids = select(DimDomain.id).where(func.lower(DimDomain.tld).in_(tld_values))
        filters.append(FactTrafficCountriesDaily.domain_id.in_(tld_domain_ids))

    return filters


def fetch_summary(session: Session, filters: list[Any]) -> CountryIntelligenceSummary:
    """Fetch summary metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    active_company = case((FactTrafficCountriesDaily.traffic > 0, FactTrafficCountriesDaily.company_id), else_=None)
    active_domain = case((FactTrafficCountriesDaily.traffic > 0, FactTrafficCountriesDaily.domain_id), else_=None)
    result = session.execute(
        select(
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('total_traffic'),
            func.count(func.distinct(active_company)).label('active_competitors'),
            func.count(func.distinct(active_domain)).label('active_domains'),
            func.count(func.distinct(FactTrafficCountriesDaily.country_id)).label('country_count'),
            func.count(func.distinct(FactTrafficCountriesDaily.date)).label('date_count'),
        ).where(*filters)
    ).one()
    summary = CountryIntelligenceSummary(
        total_traffic=safe_int(result.total_traffic),
        active_competitors=safe_int(result.active_competitors),
        active_domains=safe_int(result.active_domains),
        country_count=safe_int(result.country_count),
        date_count=safe_int(result.date_count),
    )
    return summary


def fetch_country_count(session: Session, filter_groups: list[list[Any]]) -> int:
    """Fetch distinct country count.
    Args:
        session (Session): Active database session.
        filter_groups (list[list[Any]]): SQLAlchemy filter groups."""
    country_queries = [
        select(FactTrafficCountriesDaily.country_id.label('country_id')).where(*filters) for filters in filter_groups
    ]
    country_union = union_all(*country_queries).subquery()
    country_count = session.scalar(select(func.count(func.distinct(country_union.c.country_id))))
    return safe_int(country_count)


def fetch_filter_options(
    session: Session,
    default_project_id: str,
    project_id: str | None,
    date_from: date | None,
    date_to: date | None,
    country: str | None,
    tld: str | None,
    company: str | None,
    company_domain: str | None,
    competitors: str | None,
    competitor_domain: str | None,
) -> AnalyticsFilterOptionsResponse:
    """Fetch dashboard filter options.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country values.
        tld (str | None): Requested top-level domains.
        company (str | None): Requested company identifiers.
        company_domain (str | None): Requested company domains.
        competitors (str | None): Requested competitor identifiers.
        competitor_domain (str | None): Requested competitor domains."""
    resolved_project_id = resolve_project(project_id, default_project_id)
    resolved_date_from, resolved_date_to = read_dates(session, resolved_project_id, date_from, date_to)
    resolved_countries = normalize_values(country)
    resolved_tlds = normalize_values(tld)
    resolved_company = normalize_ids(company)
    resolved_company_domains = normalize_values(company_domain)
    resolved_competitors = normalize_ids(competitors)
    resolved_competitor_domains = normalize_values(competitor_domain)
    country_filters = build_filters(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        None,
        None,
        None,
        resolved_tlds,
    )
    company_scope_active = resolved_company != [] and (
        resolved_company is not None or resolved_company_domains not in (None, [])
    )
    competitor_scope_active = resolved_competitors != [] and (
        resolved_competitors is not None or resolved_competitor_domains not in (None, [])
    )
    country_scope_filters: list[Any] = []

    if company_scope_active:
        company_scope_filters = build_filters(
            resolved_project_id,
            resolved_date_from,
            resolved_date_to,
            None,
            resolved_company,
            resolved_company_domains,
            resolved_tlds,
        )
        company_country_ids = select(FactTrafficCountriesDaily.country_id).where(*company_scope_filters).distinct()
        country_scope_filters.append(FactTrafficCountriesDaily.country_id.in_(company_country_ids))
    if competitor_scope_active:
        competitor_scope_filters = build_filters(
            resolved_project_id,
            resolved_date_from,
            resolved_date_to,
            None,
            resolved_competitors,
            resolved_competitor_domains,
            resolved_tlds,
        )
        competitor_country_ids = (
            select(FactTrafficCountriesDaily.country_id).where(*competitor_scope_filters).distinct()
        )
        country_scope_filters.append(FactTrafficCountriesDaily.country_id.in_(competitor_country_ids))
    if country_scope_filters:
        country_filters.append(or_(*country_scope_filters))

    company_filters = build_filters(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        resolved_countries,
        None,
        None,
        resolved_tlds,
    )
    tld_filters = build_filters(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        resolved_countries,
        None,
        None,
        None,
    )

    country_rows = session.execute(
        select(
            DimCountry.country_name_en.label('label'),
            DimCountry.iso3.label('value'),
        )
        .join(FactTrafficCountriesDaily, FactTrafficCountriesDaily.country_id == DimCountry.id)
        .where(*country_filters)
        .group_by(DimCountry.country_name_en, DimCountry.iso3)
        .order_by(DimCountry.country_name_en)
    ).all()
    company_rows = session.execute(
        select(
            DimCompany.name.label('label'),
            DimCompany.id.label('value'),
        )
        .join(FactTrafficCountriesDaily, FactTrafficCountriesDaily.company_id == DimCompany.id)
        .where(*company_filters)
        .group_by(DimCompany.name, DimCompany.id)
        .order_by(DimCompany.name)
    ).all()
    domain_rows = session.execute(
        select(
            DimDomain.domain.label('label'),
            DimDomain.domain.label('value'),
            DimDomain.company_id.label('company_id'),
            DimDomain.tld.label('tld'),
        )
        .join(FactTrafficCountriesDaily, FactTrafficCountriesDaily.domain_id == DimDomain.id)
        .where(*company_filters)
        .group_by(DimDomain.domain, DimDomain.company_id, DimDomain.tld)
        .order_by(DimDomain.domain)
    ).all()
    tld_rows = session.execute(
        select(DimDomain.tld.label('value'))
        .join(FactTrafficCountriesDaily, FactTrafficCountriesDaily.domain_id == DimDomain.id)
        .where(*tld_filters, DimDomain.tld.is_not(None))
        .group_by(DimDomain.tld)
        .order_by(DimDomain.tld)
    ).all()

    options = AnalyticsFilterOptionsResponse(
        countries=[FilterOption(label=row.label, value=row.value) for row in country_rows],
        tlds=[FilterOption(label=f'.{row.value}', value=row.value) for row in tld_rows],
        companies=[FilterOption(label=row.label, value=str(row.value)) for row in company_rows],
        domains=[
            DomainFilterOption(label=row.label, value=row.value, company_id=row.company_id, tld=row.tld)
            for row in domain_rows
        ],
    )
    return options


def fetch_competitors(
    session: Session,
    filters: list[Any],
    total_traffic: int,
    limit: int,
) -> list[TopCompetitor]:
    """Fetch top competitors.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        total_traffic (int): Total selected traffic.
        limit (int): Top rows limit."""
    traffic_sum = func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('traffic')
    rows = session.execute(
        select(
            FactTrafficCountriesDaily.company_id.label('company_id'),
            DimCompany.name.label('company'),
            traffic_sum,
            func.count(func.distinct(FactTrafficCountriesDaily.domain_id)).label('domains_count'),
        )
        .join(DimCompany, FactTrafficCountriesDaily.company_id == DimCompany.id)
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.company_id, DimCompany.name)
        .having(func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0) > 0)
        .order_by(desc('traffic'))
        .limit(limit)
    ).all()
    competitors = [
        TopCompetitor(
            company_id=safe_int(row.company_id),
            company=row.company,
            traffic=safe_int(row.traffic),
            traffic_share=divide_values(safe_int(row.traffic), total_traffic),
            domains_count=safe_int(row.domains_count),
        )
        for row in rows
    ]
    return competitors


def fetch_trend(session: Session, filters: list[Any]) -> list[TrafficTrendPoint]:
    """Fetch traffic trend.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    rows = session.execute(
        select(
            FactTrafficCountriesDaily.date.label('date'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('traffic'),
        )
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.date)
        .order_by(FactTrafficCountriesDaily.date)
    ).all()
    trend = [TrafficTrendPoint(date=row.date, traffic=safe_int(row.traffic)) for row in rows]
    return trend


def fetch_devices(session: Session, filters: list[Any]) -> DeviceSplit:
    """Fetch device split.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    result = session.execute(
        select(
            func.coalesce(func.sum(FactTrafficCountriesDaily.desktop_share_traffic), 0).label('desktop_traffic'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.mobile_share_traffic), 0).label('mobile_traffic'),
        ).where(*filters)
    ).one()
    desktop_traffic = safe_int(result.desktop_traffic)
    mobile_traffic = safe_int(result.mobile_traffic)
    total_device_traffic = desktop_traffic + mobile_traffic
    device_split = DeviceSplit(
        desktop_traffic=desktop_traffic,
        mobile_traffic=mobile_traffic,
        desktop_share=divide_values(desktop_traffic, total_device_traffic),
        mobile_share=divide_values(mobile_traffic, total_device_traffic),
    )
    return device_split


def fetch_bounce(session: Session, filters: list[Any]) -> BounceSummary:
    """Fetch bounce summary.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    result = session.execute(
        select(
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic_no_bounce), 0).label('no_bounce'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic_bounce), 0).label('bounce'),
        ).where(*filters)
    ).one()
    no_bounce = safe_int(result.no_bounce)
    bounce = safe_int(result.bounce)
    total_bounce_traffic = no_bounce + bounce
    bounce_summary = BounceSummary(
        no_bounce=no_bounce,
        bounce=bounce,
        bounce_rate=divide_values(bounce, total_bounce_traffic),
    )
    return bounce_summary


def fetch_engagement(session: Session, filters: list[Any]) -> EngagementMetrics:
    """Fetch engagement metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    result = session.execute(
        select(
            func.coalesce(func.sum(FactTrafficCountriesDaily.unique_visitors), 0).label('unique_visitors'),
            func.coalesce(
                func.sum(FactTrafficCountriesDaily.pages_per_visit * FactTrafficCountriesDaily.traffic),
                0,
            ).label('pages_per_visit_weighted'),
            func.coalesce(
                func.sum(FactTrafficCountriesDaily.avg_visit_duration * FactTrafficCountriesDaily.traffic),
                0,
            ).label('duration_weighted'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('traffic'),
        ).where(*filters)
    ).one()
    traffic = safe_int(result.traffic)
    engagement = EngagementMetrics(
        unique_visitors=safe_int(result.unique_visitors),
        pages_per_visit=divide_values(safe_float(result.pages_per_visit_weighted), traffic),
        avg_visit_duration=divide_values(safe_float(result.duration_weighted), traffic),
    )
    return engagement


def split_trend(trend: list[TrafficTrendPoint]) -> tuple[int, int]:
    """Split traffic trend.
    Args:
        trend (list[TrafficTrendPoint]): Daily traffic trend."""
    middle_index = len(trend) // 2
    first_half = trend[:middle_index]
    second_half = trend[middle_index:]
    first_half_traffic = sum(point.traffic for point in first_half)
    second_half_traffic = sum(point.traffic for point in second_half)
    return first_half_traffic, second_half_traffic


def message_signal(status: str) -> str:
    """Build market signal message.
    Args:
        status (str): Market signal status."""
    messages = {
        'no_data': 'No country traffic data was found for the selected filters.',
        'insufficient_data': 'Not enough dated traffic points are available for a trend signal.',
        'new_activity': 'Traffic appears only in the later part of the selected period.',
        'falling': 'Traffic decreased during the selected period.',
        'stable': 'Traffic stayed broadly stable during the selected period.',
        'promising': 'Traffic is growing and competitor concentration is not dominant.',
        'overheated': 'Traffic is growing, but the leading competitor has a dominant share.',
        'growing': 'Traffic increased during the selected period.',
        'mixed': 'Traffic movement is mixed for the selected period.',
    }
    return messages.get(status, messages['mixed'])


def build_signal(
    summary: CountryIntelligenceSummary,
    trend: list[TrafficTrendPoint],
    top_competitors: list[TopCompetitor],
    bounce: BounceSummary,
) -> MarketSignal:
    """Build market signal.
    Args:
        summary (CountryIntelligenceSummary): Summary metrics.
        trend (list[TrafficTrendPoint]): Daily traffic trend.
        top_competitors (list[TopCompetitor]): Top competitor metrics.
        bounce (BounceSummary): Bounce summary."""
    if summary.total_traffic == 0:
        return MarketSignal(status='no_data', growth_rate=0.0, message=message_signal('no_data'))
    if len(trend) < 2:
        return MarketSignal(status='insufficient_data', growth_rate=0.0, message=message_signal('insufficient_data'))

    first_half_traffic, second_half_traffic = split_trend(trend)
    if first_half_traffic == 0 and second_half_traffic > 0:
        return MarketSignal(status='new_activity', growth_rate=0.0, message=message_signal('new_activity'))

    growth_rate = divide_values(second_half_traffic - first_half_traffic, first_half_traffic)
    top_share = top_competitors[0].traffic_share if top_competitors else 0.0

    if growth_rate <= -0.10:
        status = 'falling'
    elif -0.05 <= growth_rate <= 0.05:
        status = 'stable'
    elif growth_rate >= 0.10 and top_share < 0.40 and bounce.bounce_rate < 0.55:
        status = 'promising'
    elif growth_rate >= 0.10 and top_share >= 0.50:
        status = 'overheated'
    elif growth_rate >= 0.10:
        status = 'growing'
    else:
        status = 'mixed'

    signal = MarketSignal(status=status, growth_rate=growth_rate, message=message_signal(status))
    return signal


def get_country_intelligence(
    session: Session,
    default_project_id: str,
    project_id: str | None,
    date_from: date | None,
    date_to: date | None,
    country: str | None,
    tld: str | None,
    company: str | None,
    company_domain: str | None,
    competitors: str | None,
    competitor_domain: str | None,
    limit: int | None,
) -> CountryIntelligenceResponse:
    """Get country intelligence.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country filter.
        tld (str | None): Requested top-level domains.
        company (str | None): Requested company identifiers.
        company_domain (str | None): Requested company domains.
        competitors (str | None): Requested competitor identifiers.
        competitor_domain (str | None): Requested competitor domains.
        limit (int | None): Requested top rows limit."""
    resolved_project_id = resolve_project(project_id, default_project_id)
    resolved_country = normalize_text(country, 'all')
    resolved_countries = normalize_values(resolved_country)
    normalized_tld = normalize_text(tld, 'all')
    normalized_company = normalize_text(company, 'all')
    normalized_company_domain = normalize_text(company_domain, 'all')
    normalized_competitors = normalize_text(competitors, 'all')
    normalized_competitor_domain = normalize_text(competitor_domain, 'all')
    resolved_tlds = normalize_values(normalized_tld)
    resolved_company = normalize_ids(normalized_company)
    resolved_company_domain = normalize_values(normalized_company_domain)
    resolved_competitors = normalize_ids(normalized_competitors)
    resolved_competitor_domain = normalize_values(normalized_competitor_domain)
    resolved_limit = normalize_limit(limit)
    resolved_date_from, resolved_date_to = read_dates(session, resolved_project_id, date_from, date_to)
    filters = build_filters(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        resolved_countries,
        resolved_company,
        resolved_company_domain,
        resolved_tlds,
    )
    competitor_filters = build_filters(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        resolved_countries,
        resolved_competitors,
        resolved_competitor_domain,
        resolved_tlds,
    )
    summary = fetch_summary(session, filters)
    competitor_summary = fetch_summary(session, competitor_filters)
    top_competitors = fetch_competitors(
        session,
        competitor_filters,
        competitor_summary.total_traffic,
        resolved_limit,
    )
    traffic_trend = fetch_trend(session, filters)
    competitor_traffic_trend = fetch_trend(session, competitor_filters)
    device_split = fetch_devices(session, filters)
    competitor_device_split = fetch_devices(session, competitor_filters)
    bounce = fetch_bounce(session, filters)
    competitor_bounce = fetch_bounce(session, competitor_filters)
    engagement = fetch_engagement(session, filters)
    competitor_engagement = fetch_engagement(session, competitor_filters)
    selected_country_count = fetch_country_count(session, [filters, competitor_filters])
    market_signal = build_signal(summary, traffic_trend, top_competitors, bounce)
    competitor_market_signal = build_signal(
        competitor_summary,
        competitor_traffic_trend,
        top_competitors,
        competitor_bounce,
    )

    response = CountryIntelligenceResponse(
        filters=CountryIntelligenceFilters(
            project_id=resolved_project_id,
            date_from=resolved_date_from,
            date_to=resolved_date_to,
            country=resolved_country,
            tld=normalized_tld,
            company=normalized_company,
            company_domain=normalized_company_domain,
            competitors=normalized_competitors,
            competitor_domain=normalized_competitor_domain,
        ),
        selected_country_count=selected_country_count,
        summary=summary,
        competitor_summary=competitor_summary,
        top_competitors=top_competitors,
        traffic_trend=traffic_trend,
        competitor_traffic_trend=competitor_traffic_trend,
        device_split=device_split,
        competitor_device_split=competitor_device_split,
        bounce=bounce,
        competitor_bounce=competitor_bounce,
        engagement=engagement,
        competitor_engagement=competitor_engagement,
        market_signal=market_signal,
        competitor_market_signal=competitor_market_signal,
    )
    return response
