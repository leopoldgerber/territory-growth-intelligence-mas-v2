from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import and_, case, false, func, or_, select, true
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import (
    divide_values,
    normalize_ids,
    normalize_limit,
    normalize_text,
    normalize_values,
    resolve_project,
    safe_int,
)
from app.models.tables import (
    DimCompany,
    DimCountry,
    DimDomain,
    FactJourneySourcesDaily,
    FactTrafficCountriesDaily,
    FactTrafficSourcesDaily,
)
from app.schemas.analytics import (
    ChannelIntelligenceFilters,
    ChannelIntelligenceResponse,
    ChannelMixItem,
    ChannelScopeAnalytics,
    ChannelSkew,
    ChannelSummary,
    CompetitorChannelDependency,
    OpportunitySignal,
    PaidOrganicSummary,
    SourceBreakdownItem,
    TopSourceItem,
    TrafficBreakdownItem,
)

CHANNELS = ('direct', 'search', 'paid', 'referral', 'social')
COUNTRY_SCOPE_NOTE = (
    'Country filter limits channel analysis to domains active in the selected countries. '
    'Channel metrics are based on domain-level source data.'
)


def read_channel_dates(
    session: Session,
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
) -> tuple[date | None, date | None]:
    """Read effective channel date range.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date."""
    source_dates = session.execute(
        select(
            func.min(FactTrafficSourcesDaily.date),
            func.max(FactTrafficSourcesDaily.date),
        ).where(FactTrafficSourcesDaily.project_id == project_id)
    ).one()
    journey_dates = session.execute(
        select(
            func.min(FactJourneySourcesDaily.date),
            func.max(FactJourneySourcesDaily.date),
        ).where(FactJourneySourcesDaily.project_id == project_id)
    ).one()
    minimum_dates = [value for value in (source_dates[0], journey_dates[0]) if value is not None]
    maximum_dates = [value for value in (source_dates[1], journey_dates[1]) if value is not None]
    effective_date_from = date_from if date_from is not None else min(minimum_dates, default=None)
    effective_date_to = date_to if date_to is not None else max(maximum_dates, default=None)
    return effective_date_from, effective_date_to


def build_scope_filter(
    fact_model: Any,
    company: str,
    company_domain: str,
    competitors: str,
    competitor_domain: str,
) -> Any:
    """Build combined company scope filter.
    Args:
        fact_model (Any): SQLAlchemy fact model.
        company (str): Selected company identifiers.
        company_domain (str): Selected company domains.
        competitors (str): Selected competitor identifiers.
        competitor_domain (str): Selected competitor domains."""
    company_filter = build_single_scope(fact_model, company, company_domain)
    competitor_filter = build_single_scope(fact_model, competitors, competitor_domain)
    company_explicit = normalize_text(company, 'all').lower() != 'all' or normalize_text(
        company_domain,
        'all',
    ).lower() != 'all'
    competitor_explicit = normalize_text(competitors, 'all').lower() != 'all' or normalize_text(
        competitor_domain,
        'all',
    ).lower() != 'all'
    explicit_filters: list[Any] = []
    if company_explicit and normalize_text(company, 'all').lower() != 'none':
        explicit_filters.append(company_filter)
    if competitor_explicit and normalize_text(competitors, 'all').lower() != 'none':
        explicit_filters.append(competitor_filter)
    if explicit_filters:
        return or_(*explicit_filters)
    if normalize_text(company, 'all').lower() == 'none' and normalize_text(competitors, 'all').lower() == 'none':
        return false()
    return true()


def build_single_scope(fact_model: Any, company: str, domain: str) -> Any:
    """Build one company scope filter.
    Args:
        fact_model (Any): SQLAlchemy fact model.
        company (str): Selected company identifiers.
        domain (str): Selected company domains."""
    company_ids = normalize_ids(company)
    domains = normalize_values(domain)
    if company_ids == []:
        return false()
    conditions: list[Any] = []
    if company_ids is not None:
        conditions.append(fact_model.company_id.in_(company_ids))
    if domains is not None:
        domain_values = [domain_value.lower() for domain_value in domains]
        domain_ids = select(DimDomain.id).where(func.lower(DimDomain.domain).in_(domain_values))
        conditions.append(fact_model.domain_id.in_(domain_ids) if domains else false())
    return and_(*conditions) if conditions else true()


def build_country_scope(
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
    countries: list[str] | None,
) -> Any | None:
    """Build active country domain scope.
    Args:
        project_id (UUID): Project identifier.
        date_from (date | None): Effective start date.
        date_to (date | None): Effective end date.
        countries (list[str] | None): Selected country values."""
    if countries is None:
        return None
    filters: list[Any] = [
        FactTrafficCountriesDaily.project_id == project_id,
        FactTrafficCountriesDaily.traffic > 0,
    ]
    if date_from is not None:
        filters.append(FactTrafficCountriesDaily.date >= date_from)
    if date_to is not None:
        filters.append(FactTrafficCountriesDaily.date <= date_to)
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
    return select(FactTrafficCountriesDaily.domain_id).where(*filters).distinct()


def build_fact_filters(
    fact_model: Any,
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
    tlds: list[str] | None,
    country_domains: Any | None,
    scope_filter: Any,
) -> list[Any]:
    """Build channel fact filters.
    Args:
        fact_model (Any): SQLAlchemy fact model.
        project_id (UUID): Project identifier.
        date_from (date | None): Effective start date.
        date_to (date | None): Effective end date.
        tlds (list[str] | None): Selected top-level domains.
        country_domains (Any | None): Active country domain query.
        scope_filter (Any): Combined company scope expression."""
    filters: list[Any] = [fact_model.project_id == project_id, scope_filter]
    if date_from is not None:
        filters.append(fact_model.date >= date_from)
    if date_to is not None:
        filters.append(fact_model.date <= date_to)
    if tlds is not None:
        tld_values = [tld.lower().lstrip('.') for tld in tlds]
        domain_ids = select(DimDomain.id).where(func.lower(DimDomain.tld).in_(tld_values))
        filters.append(fact_model.domain_id.in_(domain_ids) if tlds else false())
    if country_domains is not None:
        filters.append(fact_model.domain_id.in_(country_domains))
    return filters


def fetch_channel_totals(session: Session, filters: list[Any]) -> dict[str, int]:
    """Fetch aggregate channel totals.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    result = session.execute(
        select(
            func.coalesce(func.sum(FactTrafficSourcesDaily.direct), 0).label('direct'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.search), 0).label('search'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.paid), 0).label('paid'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.referral), 0).label('referral'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.social), 0).label('social'),
            func.count(func.distinct(FactTrafficSourcesDaily.company_id)).label('competitors_count'),
            func.count(func.distinct(FactTrafficSourcesDaily.domain_id)).label('domains_count'),
        ).where(*filters)
    ).one()
    totals = {channel: safe_int(getattr(result, channel)) for channel in CHANNELS}
    totals['competitors_count'] = safe_int(result.competitors_count)
    totals['domains_count'] = safe_int(result.domains_count)
    return totals


def build_channel_mix(totals: dict[str, int]) -> list[ChannelMixItem]:
    """Build channel mix metrics.
    Args:
        totals (dict[str, int]): Aggregate channel totals."""
    total_traffic = sum(totals[channel] for channel in CHANNELS)
    return [
        ChannelMixItem(
            channel=channel,
            traffic=totals[channel],
            share=divide_values(totals[channel], total_traffic),
        )
        for channel in CHANNELS
    ]


def classify_dependency(dominant_share: float) -> str:
    """Classify channel dependency.
    Args:
        dominant_share (float): Dominant channel traffic share."""
    if dominant_share >= 0.60:
        return 'high'
    if dominant_share >= 0.40:
        return 'medium'
    return 'low'


def fetch_company_channels(session: Session, filters: list[Any]) -> list[dict[str, Any]]:
    """Fetch company channel totals.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    rows = session.execute(
        select(
            FactTrafficSourcesDaily.company_id.label('company_id'),
            DimCompany.name.label('company'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.direct), 0).label('direct'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.search), 0).label('search'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.paid), 0).label('paid'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.referral), 0).label('referral'),
            func.coalesce(func.sum(FactTrafficSourcesDaily.social), 0).label('social'),
        )
        .join(DimCompany, FactTrafficSourcesDaily.company_id == DimCompany.id)
        .where(*filters)
        .group_by(FactTrafficSourcesDaily.company_id, DimCompany.name)
    ).all()
    company_rows = [
        {
            'company_id': safe_int(row.company_id),
            'company': row.company,
            **{channel: safe_int(getattr(row, channel)) for channel in CHANNELS},
        }
        for row in rows
    ]
    return sorted(company_rows, key=lambda row: sum(row[channel] for channel in CHANNELS), reverse=True)


def build_dependencies(rows: list[dict[str, Any]], limit: int) -> list[CompetitorChannelDependency]:
    """Build company channel dependencies.
    Args:
        rows (list[dict[str, Any]]): Company channel totals.
        limit (int): Result row limit."""
    dependencies: list[CompetitorChannelDependency] = []
    for row in rows[:limit]:
        total_traffic = sum(row[channel] for channel in CHANNELS)
        dominant_channel = max(CHANNELS, key=lambda channel: row[channel]) if total_traffic > 0 else None
        dominant_share = divide_values(row[dominant_channel], total_traffic) if dominant_channel else 0.0
        dependencies.append(
            CompetitorChannelDependency(
                company_id=row['company_id'],
                company=row['company'],
                total_traffic=total_traffic,
                dominant_channel=dominant_channel,
                dominant_channel_share=dominant_share,
                direct_share=divide_values(row['direct'], total_traffic),
                search_share=divide_values(row['search'], total_traffic),
                paid_share=divide_values(row['paid'], total_traffic),
                referral_share=divide_values(row['referral'], total_traffic),
                social_share=divide_values(row['social'], total_traffic),
                dependency_level=classify_dependency(dominant_share),
            )
        )
    return dependencies


def build_channel_skews(
    dependencies: list[CompetitorChannelDependency],
    limit: int,
) -> list[ChannelSkew]:
    """Build channel skew signals.
    Args:
        dependencies (list[CompetitorChannelDependency]): Company dependency metrics.
        limit (int): Result row limit."""
    rules = (
        ('direct', 'direct_share', 0.60, 'brand_dependency', 'Direct traffic dominates this company channel mix.'),
        ('search', 'search_share', 0.60, 'seo_dependency', 'Search traffic dominates this company channel mix.'),
        ('paid', 'paid_share', 0.35, 'paid_dependency', 'Paid traffic has a concentrated role in this company mix.'),
        (
            'referral',
            'referral_share',
            0.30,
            'referral_dependency',
            'Referral traffic has a concentrated role in this company mix.',
        ),
        ('social', 'social_share', 0.25, 'social_dependency', 'Social traffic has a concentrated role in this mix.'),
    )
    skews: list[ChannelSkew] = []
    for dependency in dependencies:
        matched = False
        for channel, field_name, threshold, signal, message in rules:
            share = float(getattr(dependency, field_name))
            if share >= threshold:
                skews.append(
                    ChannelSkew(
                        company=dependency.company,
                        channel=channel,
                        share=share,
                        signal=signal,
                        message=message,
                    )
                )
                matched = True
        if not matched and dependency.dominant_channel_share < 0.40:
            skews.append(
                ChannelSkew(
                    company=dependency.company,
                    channel=dependency.dominant_channel or 'none',
                    share=dependency.dominant_channel_share,
                    signal='balanced_mix',
                    message='No single channel represents 40% or more of this company mix.',
                )
            )
    return skews[:limit]


def fetch_journey_rows(session: Session, filters: list[Any]) -> list[dict[str, Any]]:
    """Fetch normalized journey source rows.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    source_type = func.lower(func.trim(FactJourneySourcesDaily.source_type))
    traffic_type = func.coalesce(
        func.nullif(func.lower(func.trim(FactJourneySourcesDaily.traffic_type)), ''),
        'unknown',
    )
    search_source = case(
        (
            or_(
                FactJourneySourcesDaily.search_source.is_(None),
                func.trim(FactJourneySourcesDaily.search_source).in_(('', '__empty__')),
            ),
            'No source',
        ),
        else_=func.trim(FactJourneySourcesDaily.search_source),
    )
    rows = session.execute(
        select(
            source_type.label('source_type'),
            traffic_type.label('traffic_type'),
            search_source.label('search_source'),
            func.coalesce(func.sum(FactJourneySourcesDaily.traffic), 0).label('traffic'),
        )
        .where(*filters)
        .group_by(source_type, traffic_type, search_source)
    ).all()
    return [
        {
            'source_type': row.source_type or 'unknown',
            'traffic_type': row.traffic_type or 'unknown',
            'search_source': row.search_source or 'No source',
            'traffic': safe_int(row.traffic),
        }
        for row in rows
    ]


def build_paid_organic(rows: list[dict[str, Any]]) -> PaidOrganicSummary:
    """Build paid and organic split.
    Args:
        rows (list[dict[str, Any]]): Normalized journey source rows."""
    paid_traffic = 0
    organic_traffic = 0
    unknown_traffic = 0
    for row in rows:
        if row['traffic_type'] == 'paid' or row['source_type'] == 'paid':
            paid_traffic += row['traffic']
        elif row['traffic_type'] == 'organic':
            organic_traffic += row['traffic']
        else:
            unknown_traffic += row['traffic']
    total_traffic = paid_traffic + organic_traffic + unknown_traffic
    return PaidOrganicSummary(
        paid_traffic=paid_traffic,
        organic_traffic=organic_traffic,
        unknown_traffic=unknown_traffic,
        paid_share=divide_values(paid_traffic, total_traffic),
        organic_share=divide_values(organic_traffic, total_traffic),
        unknown_share=divide_values(unknown_traffic, total_traffic),
    )


def build_breakdowns(
    rows: list[dict[str, Any]],
) -> tuple[list[SourceBreakdownItem], list[TrafficBreakdownItem]]:
    """Build journey source breakdowns.
    Args:
        rows (list[dict[str, Any]]): Normalized journey source rows."""
    total_traffic = sum(row['traffic'] for row in rows)
    source_totals: dict[str, int] = {}
    traffic_totals: dict[str, int] = {}
    for row in rows:
        source_totals[row['source_type']] = source_totals.get(row['source_type'], 0) + row['traffic']
        traffic_totals[row['traffic_type']] = traffic_totals.get(row['traffic_type'], 0) + row['traffic']
    source_breakdown = [
        SourceBreakdownItem(source_type=key, traffic=value, share=divide_values(value, total_traffic))
        for key, value in sorted(source_totals.items(), key=lambda item: item[1], reverse=True)
    ]
    traffic_breakdown = [
        TrafficBreakdownItem(traffic_type=key, traffic=value, share=divide_values(value, total_traffic))
        for key, value in sorted(traffic_totals.items(), key=lambda item: item[1], reverse=True)
    ]
    return source_breakdown, traffic_breakdown


def build_top_sources(rows: list[dict[str, Any]], limit: int) -> list[TopSourceItem]:
    """Build top journey sources.
    Args:
        rows (list[dict[str, Any]]): Normalized journey source rows.
        limit (int): Result row limit."""
    total_traffic = sum(row['traffic'] for row in rows)
    sorted_rows = sorted(rows, key=lambda row: row['traffic'], reverse=True)
    return [
        TopSourceItem(
            source_type=row['source_type'],
            traffic_type=row['traffic_type'],
            search_source=row['search_source'],
            traffic=row['traffic'],
            share=divide_values(row['traffic'], total_traffic),
        )
        for row in sorted_rows[:limit]
    ]


def build_opportunity_signals(channel_mix: list[ChannelMixItem]) -> list[OpportunitySignal]:
    """Build neutral channel signals.
    Args:
        channel_mix (list[ChannelMixItem]): Aggregate channel mix."""
    shares = {item.channel: item.share for item in channel_mix}
    signals: list[OpportunitySignal] = []
    rules = (
        ('search', 0.40, 'seo', 'high_search_share', 'Search is a major acquisition channel in the selected scope.'),
        ('paid', 0.20, 'paid', 'meaningful_paid_share', 'Paid traffic has meaningful presence in this scope.'),
        (
            'referral',
            0.15,
            'partnerships',
            'visible_referral_share',
            'Referral traffic is visible and may indicate partnership-driven acquisition.',
        ),
        ('social', 0.15, 'social', 'visible_social_share', 'Social traffic has meaningful presence in this scope.'),
        ('direct', 0.50, 'brand', 'high_direct_share', 'Direct traffic is a major acquisition channel in this scope.'),
    )
    for channel, threshold, signal_type, signal, message in rules:
        if shares.get(channel, 0.0) >= threshold:
            signals.append(OpportunitySignal(type=signal_type, signal=signal, message=message))
    if sum(item.traffic for item in channel_mix) > 0:
        for item in channel_mix:
            if item.share <= 0.03:
                signals.append(
                    OpportunitySignal(
                        type='channel_gap',
                        signal=f'low_{item.channel}_share',
                        message=f'{item.channel.title()} represents 3% or less of traffic in the selected scope.',
                    )
                )
    return signals


def build_scope_analytics(
    session: Session,
    source_filters: list[Any],
    journey_filters: list[Any],
    limit: int,
) -> ChannelScopeAnalytics:
    """Build one channel analytics scope.
    Args:
        session (Session): Active database session.
        source_filters (list[Any]): Traffic source filter expressions.
        journey_filters (list[Any]): Journey source filter expressions.
        limit (int): Requested result limit."""
    totals = fetch_channel_totals(session, source_filters)
    channel_mix = build_channel_mix(totals)
    total_traffic = sum(item.traffic for item in channel_mix)
    dominant_item = max(channel_mix, key=lambda item: item.traffic) if total_traffic > 0 else None
    company_rows = fetch_company_channels(session, source_filters)
    dependencies = build_dependencies(company_rows, limit)
    journey_rows = fetch_journey_rows(session, journey_filters)
    paid_organic = build_paid_organic(journey_rows)
    source_breakdown, traffic_breakdown = build_breakdowns(journey_rows)
    return ChannelScopeAnalytics(
        summary=ChannelSummary(
            total_traffic=total_traffic,
            dominant_channel=dominant_item.channel if dominant_item else None,
            dominant_channel_share=dominant_item.share if dominant_item else 0.0,
            paid_share=paid_organic.paid_share,
            organic_share=paid_organic.organic_share,
            competitors_count=totals['competitors_count'],
            domains_count=totals['domains_count'],
        ),
        channel_mix=channel_mix if total_traffic > 0 else [],
        company_channel_dependency=dependencies,
        channel_skews=build_channel_skews(dependencies, limit),
        paid_organic=paid_organic,
        source_type_breakdown=source_breakdown,
        traffic_type_breakdown=traffic_breakdown,
        top_sources=build_top_sources(journey_rows, limit),
        opportunity_signals=build_opportunity_signals(channel_mix)[:limit],
    )


def get_channel_intelligence(
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
) -> ChannelIntelligenceResponse:
    """Get channel intelligence analytics.
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
        competitor_domain (str | None): Requested competitor domains.
        limit (int | None): Requested result limit."""
    resolved_project_id = resolve_project(project_id, default_project_id)
    normalized_country = normalize_text(country, 'all')
    normalized_tld = normalize_text(tld, 'all')
    normalized_company = normalize_text(company, 'all')
    normalized_company_domain = normalize_text(company_domain, 'all')
    normalized_competitors = normalize_text(competitors, 'all')
    normalized_competitor_domain = normalize_text(competitor_domain, 'all')
    resolved_date_from, resolved_date_to = read_channel_dates(
        session,
        resolved_project_id,
        date_from,
        date_to,
    )
    countries = normalize_values(normalized_country)
    country_domains = build_country_scope(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        countries,
    )
    resolved_limit = normalize_limit(limit)
    tlds = normalize_values(normalized_tld)
    combined_scopes = all(
        value.lower() == 'all'
        for value in (
            normalized_company,
            normalized_company_domain,
            normalized_competitors,
            normalized_competitor_domain,
        )
    )

    def read_scope(company_value: str, domain_value: str) -> ChannelScopeAnalytics:
        """Read one separated channel scope.
        Args:
            company_value (str): Selected company identifiers.
            domain_value (str): Selected domain values."""
        source_filters = build_fact_filters(
            FactTrafficSourcesDaily,
            resolved_project_id,
            resolved_date_from,
            resolved_date_to,
            tlds,
            country_domains,
            build_single_scope(FactTrafficSourcesDaily, company_value, domain_value),
        )
        journey_filters = build_fact_filters(
            FactJourneySourcesDaily,
            resolved_project_id,
            resolved_date_from,
            resolved_date_to,
            tlds,
            country_domains,
            build_single_scope(FactJourneySourcesDaily, company_value, domain_value),
        )
        return build_scope_analytics(session, source_filters, journey_filters, resolved_limit)

    overall_scope = read_scope('all', 'all') if combined_scopes else None
    company_scope = (
        None if combined_scopes or normalized_company.lower() == 'none' else read_scope(
            normalized_company,
            normalized_company_domain,
        )
    )
    competitor_scope = (
        None if combined_scopes or normalized_competitors.lower() == 'none' else read_scope(
            normalized_competitors,
            normalized_competitor_domain,
        )
    )
    return ChannelIntelligenceResponse(
        filters=ChannelIntelligenceFilters(
            project_id=resolved_project_id,
            date_from=resolved_date_from,
            date_to=resolved_date_to,
            country=normalized_country,
            tld=normalized_tld,
            company=normalized_company,
            company_domain=normalized_company_domain,
            competitors=normalized_competitors,
            competitor_domain=normalized_competitor_domain,
        ),
        scope_note=COUNTRY_SCOPE_NOTE if countries is not None else None,
        combined_scopes=combined_scopes,
        overall_scope=overall_scope,
        company_scope=company_scope,
        competitor_scope=competitor_scope,
    )
