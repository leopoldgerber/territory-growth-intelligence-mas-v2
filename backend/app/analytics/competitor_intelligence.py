from datetime import date, timedelta
from typing import Any

from sqlalchemy import case, false, func, select
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import (
    build_filters,
    divide_values,
    normalize_ids,
    normalize_limit,
    normalize_text,
    normalize_values,
    read_dates,
    resolve_project,
    safe_int,
)
from app.models.tables import DimCountry, FactTrafficCountriesDaily
from app.schemas.analytics import (
    CompetitorCountryMetric,
    CompetitorDependency,
    CompetitorIntelligenceFilters,
    CompetitorIntelligenceResponse,
    CompetitorSummary,
    MarketWindow,
    PresenceStability,
)


def calculate_growth(first_traffic: int, second_traffic: int) -> float:
    """Calculate traffic growth.
    Args:
        first_traffic (int): Traffic in the first period half.
        second_traffic (int): Traffic in the second period half."""
    if first_traffic == 0:
        return 0.0
    return divide_values(second_traffic - first_traffic, first_traffic)


def classify_growth(first_traffic: int, second_traffic: int, total_traffic: int) -> str:
    """Classify traffic growth.
    Args:
        first_traffic (int): Traffic in the first period half.
        second_traffic (int): Traffic in the second period half.
        total_traffic (int): Total country traffic."""
    if total_traffic == 0:
        return 'no_data'
    if first_traffic == 0 and second_traffic > 0:
        return 'new_activity'
    growth_rate = calculate_growth(first_traffic, second_traffic)
    if growth_rate >= 0.10:
        return 'growing'
    if growth_rate <= -0.10:
        return 'declining'
    return 'stable'


def classify_dependency(top1_share: float, top3_share: float) -> str:
    """Classify country dependency.
    Args:
        top1_share (float): Leading country traffic share.
        top3_share (float): Top three countries traffic share."""
    if top1_share >= 0.50 or top3_share >= 0.80:
        return 'high'
    if top1_share >= 0.30 or top3_share >= 0.60:
        return 'medium'
    return 'low'


def classify_stability(stability_rate: float) -> str:
    """Classify presence stability.
    Args:
        stability_rate (float): Active-day share in the selected period."""
    if stability_rate >= 0.80:
        return 'stable'
    if stability_rate >= 0.40:
        return 'irregular'
    return 'weak'


def fetch_country_rows(
    session: Session,
    filters: list[Any],
    split_date: date | None,
) -> list[dict[str, Any]]:
    """Fetch competitor country aggregates.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date | None): Last date in the first period half."""
    first_condition = FactTrafficCountriesDaily.date <= split_date if split_date is not None else false()
    second_condition = FactTrafficCountriesDaily.date > split_date if split_date is not None else false()
    rows = session.execute(
        select(
            FactTrafficCountriesDaily.country_id.label('country_id'),
            DimCountry.country_name_en.label('country'),
            DimCountry.iso3.label('country_code'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('traffic'),
            func.coalesce(
                func.sum(case((first_condition, FactTrafficCountriesDaily.traffic), else_=0)),
                0,
            ).label('first_traffic'),
            func.coalesce(
                func.sum(case((second_condition, FactTrafficCountriesDaily.traffic), else_=0)),
                0,
            ).label('second_traffic'),
        )
        .join(DimCountry, FactTrafficCountriesDaily.country_id == DimCountry.id)
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.country_id, DimCountry.country_name_en, DimCountry.iso3)
        .having(func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0) > 0)
        .order_by(func.sum(FactTrafficCountriesDaily.traffic).desc())
    ).all()
    return [
        {
            'country_id': safe_int(row.country_id),
            'country': row.country,
            'country_code': row.country_code,
            'traffic': safe_int(row.traffic),
            'first_traffic': safe_int(row.first_traffic),
            'second_traffic': safe_int(row.second_traffic),
        }
        for row in rows
    ]


def build_country_metrics(rows: list[dict[str, Any]], total_traffic: int) -> list[CompetitorCountryMetric]:
    """Build country metrics.
    Args:
        rows (list[dict[str, Any]]): Country aggregate rows.
        total_traffic (int): Total competitor traffic."""
    metrics: list[CompetitorCountryMetric] = []
    for rank, row in enumerate(rows, start=1):
        traffic_share = divide_values(row['traffic'], total_traffic)
        growth_status = classify_growth(row['first_traffic'], row['second_traffic'], row['traffic'])
        if traffic_share >= 0.15 or rank <= 3:
            market_status = 'anchor'
        elif traffic_share < 0.05:
            market_status = 'peripheral'
        else:
            market_status = 'established'
        metrics.append(
            CompetitorCountryMetric(
                country_id=row['country_id'],
                country=row['country'],
                country_code=row['country_code'],
                traffic=row['traffic'],
                traffic_share=traffic_share,
                growth_rate=calculate_growth(row['first_traffic'], row['second_traffic']),
                growth_status=growth_status,
                status=market_status,
            )
        )
    return metrics


def build_market_windows(
    metrics: list[CompetitorCountryMetric],
    dependency: CompetitorDependency,
    stability: PresenceStability,
) -> list[MarketWindow]:
    """Build analytical market windows.
    Args:
        metrics (list[CompetitorCountryMetric]): Country metrics.
        dependency (CompetitorDependency): Country dependency metrics.
        stability (PresenceStability): Presence stability metrics."""
    windows: list[MarketWindow] = []
    for metric in metrics:
        if metric.growth_status == 'declining':
            windows.append(
                MarketWindow(
                    country=metric.country,
                    signal='declining_presence',
                    message='Competitor traffic is declining in this country during the selected period.',
                )
            )
        if metric.traffic_share < 0.05 and metric.growth_rate >= 0.20:
            windows.append(
                MarketWindow(
                    country=metric.country,
                    signal='small_but_growing',
                    message='Traffic share is small, while competitor traffic is growing in this country.',
                )
            )
    if stability.status == 'weak':
        windows.append(
            MarketWindow(
                country='Selected markets',
                signal='low_stability',
                message='Competitor presence is active on fewer than 40% of days in the selected period.',
            )
        )
    if dependency.dependency_level == 'high':
        windows.append(
            MarketWindow(
                country=metrics[0].country if metrics else 'Selected markets',
                signal='high_dependency',
                message='Competitor traffic is highly concentrated in one or three leading countries.',
            )
        )
    return windows


def get_competitor_intelligence(
    session: Session,
    default_project_id: str,
    project_id: str | None,
    date_from: date | None,
    date_to: date | None,
    country: str | None,
    tld: str | None,
    competitors: str | None,
    competitor_domain: str | None,
    limit: int | None,
) -> CompetitorIntelligenceResponse:
    """Get competitor intelligence.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country values.
        tld (str | None): Requested top-level domains.
        competitors (str | None): Requested competitor identifiers.
        competitor_domain (str | None): Requested competitor domains.
        limit (int | None): Requested country list limit."""
    resolved_project_id = resolve_project(project_id, default_project_id)
    normalized_country = normalize_text(country, 'all')
    normalized_tld = normalize_text(tld, 'all')
    normalized_competitors = normalize_text(competitors, 'all')
    normalized_domain = normalize_text(competitor_domain, 'all')
    resolved_date_from, resolved_date_to = read_dates(session, resolved_project_id, date_from, date_to)
    filters = build_filters(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        normalize_values(normalized_country),
        normalize_ids(normalized_competitors),
        normalize_values(normalized_domain),
        normalize_values(normalized_tld),
    )
    period_days = (
        (resolved_date_to - resolved_date_from).days + 1
        if resolved_date_from is not None and resolved_date_to is not None
        else 0
    )
    split_date = (
        resolved_date_from + timedelta(days=(period_days - 1) // 2)
        if resolved_date_from is not None and period_days > 0
        else None
    )
    rows = fetch_country_rows(session, filters, split_date)
    total_traffic = sum(row['traffic'] for row in rows)
    metrics = build_country_metrics(rows, total_traffic)
    active_domains = session.scalar(
        select(func.count(func.distinct(FactTrafficCountriesDaily.domain_id))).where(
            *filters,
            FactTrafficCountriesDaily.traffic > 0,
        )
    )
    active_days = session.scalar(
        select(func.count(func.distinct(FactTrafficCountriesDaily.date))).where(
            *filters,
            FactTrafficCountriesDaily.traffic > 0,
        )
    )
    top1_share = metrics[0].traffic_share if metrics else 0.0
    top3_share = sum(metric.traffic_share for metric in metrics[:3])
    dependency = CompetitorDependency(
        top1_country_share=top1_share,
        top3_country_share=top3_share,
        dependency_level=classify_dependency(top1_share, top3_share),
    )
    stability_rate = divide_values(safe_int(active_days), period_days)
    stability = PresenceStability(
        active_days=safe_int(active_days),
        period_days=period_days,
        stability_rate=stability_rate,
        status=classify_stability(stability_rate),
    )
    first_total = sum(row['first_traffic'] for row in rows)
    second_total = sum(row['second_traffic'] for row in rows)
    summary = CompetitorSummary(
        total_traffic=total_traffic,
        active_countries=len(metrics),
        active_domains=safe_int(active_domains),
        top_country=metrics[0].country if metrics else None,
        top_country_share=top1_share,
        growth_rate=calculate_growth(first_total, second_total),
    )
    resolved_limit = normalize_limit(limit)
    response = CompetitorIntelligenceResponse(
        filters=CompetitorIntelligenceFilters(
            project_id=resolved_project_id,
            date_from=resolved_date_from,
            date_to=resolved_date_to,
            competitors=normalized_competitors,
            competitor_domain=normalized_domain,
            country=normalized_country,
            tld=normalized_tld,
        ),
        summary=summary,
        top_countries=metrics[:resolved_limit],
        growing_countries=[
            metric for metric in metrics if metric.growth_status in {'growing', 'new_activity'}
        ][:resolved_limit],
        declining_countries=[
            metric for metric in metrics if metric.growth_status == 'declining'
        ][:resolved_limit],
        anchor_markets=[metric for metric in metrics if metric.status == 'anchor'][:resolved_limit],
        peripheral_markets=[metric for metric in metrics if metric.status == 'peripheral'][:resolved_limit],
        dependency=dependency,
        presence_stability=stability,
        market_windows=build_market_windows(metrics, dependency, stability)[:resolved_limit],
    )
    return response
