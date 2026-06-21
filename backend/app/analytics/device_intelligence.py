from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import build_country_scope, build_fact_filters, build_single_scope
from app.analytics.country_intelligence import (
    divide_values,
    normalize_limit,
    normalize_text,
    normalize_values,
    resolve_project,
    safe_float,
    safe_int,
)
from app.models.tables import DimCompany, FactDeviceTrendsDaily
from app.schemas.analytics import (
    CompetitorDeviceQuality,
    DeviceBounceSplit,
    DeviceIntelligenceFilters,
    DeviceIntelligenceResponse,
    DeviceQuality,
    DeviceScopeAnalytics,
    DeviceSignal,
    DeviceSummary,
    DeviceTrendPoint,
)

COUNTRY_SCOPE_NOTE = (
    'Country filter limits device analysis to domains active in the selected countries. '
    'Device metrics are based on domain-level data.'
)


def read_device_dates(
    session: Session,
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
) -> tuple[date | None, date | None]:
    """Read effective device date range.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date."""
    result = session.execute(
        select(
            func.min(FactDeviceTrendsDaily.date),
            func.max(FactDeviceTrendsDaily.date),
        ).where(FactDeviceTrendsDaily.project_id == project_id)
    ).one()
    effective_date_from = date_from if date_from is not None else result[0]
    effective_date_to = date_to if date_to is not None else result[1]
    return effective_date_from, effective_date_to


def calculate_quality(duration: float, bounce_rate: float) -> float:
    """Calculate comparative device quality.
    Args:
        duration (float): Weighted average duration in seconds.
        bounce_rate (float): Device bounce rate."""
    duration_score = min(max(duration, 0.0) / 180.0, 1.0)
    no_bounce_rate = min(max(1.0 - bounce_rate, 0.0), 1.0)
    return duration_score * 0.5 + no_bounce_rate * 0.5


def fetch_device_totals(
    session: Session,
    filters: list[Any],
    split_date: date | None,
) -> dict[str, int | float]:
    """Fetch aggregate device totals.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date | None): Last date in the first period half."""
    first_condition = FactDeviceTrendsDaily.date <= split_date if split_date is not None else False
    second_condition = FactDeviceTrendsDaily.date > split_date if split_date is not None else False
    result = session.execute(
        select(
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_devices), 0).label('visits_total'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_desktop), 0).label('desktop_visits'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_mobile), 0).label('mobile_visits'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.unique_devices), 0).label('unique_total'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.unique_desktop), 0).label('desktop_unique'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.unique_mobile), 0).label('mobile_unique'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.desktop_bounce), 0).label('desktop_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.desktop_no_bounce), 0).label('desktop_no_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.mobile_bounce), 0).label('mobile_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.mobile_no_bounce), 0).label('mobile_no_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.all_bounce), 0).label('total_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.all_no_bounce), 0).label('total_no_bounce'),
            func.coalesce(
                func.sum(FactDeviceTrendsDaily.duration_desktop * FactDeviceTrendsDaily.visits_desktop),
                0,
            ).label('desktop_duration_weighted'),
            func.coalesce(
                func.sum(FactDeviceTrendsDaily.duration_mobile * FactDeviceTrendsDaily.visits_mobile),
                0,
            ).label('mobile_duration_weighted'),
            func.coalesce(
                func.sum(FactDeviceTrendsDaily.duration_devices * FactDeviceTrendsDaily.visits_devices),
                0,
            ).label('duration_weighted'),
            func.coalesce(
                func.sum(case((first_condition, FactDeviceTrendsDaily.visits_mobile), else_=0)),
                0,
            ).label('first_mobile'),
            func.coalesce(
                func.sum(case((second_condition, FactDeviceTrendsDaily.visits_mobile), else_=0)),
                0,
            ).label('second_mobile'),
        ).where(*filters)
    ).one()
    integer_fields = (
        'visits_total',
        'desktop_visits',
        'mobile_visits',
        'unique_total',
        'desktop_unique',
        'mobile_unique',
        'desktop_bounce',
        'desktop_no_bounce',
        'mobile_bounce',
        'mobile_no_bounce',
        'total_bounce',
        'total_no_bounce',
        'first_mobile',
        'second_mobile',
    )
    totals: dict[str, int | float] = {field: safe_int(getattr(result, field)) for field in integer_fields}
    totals['desktop_duration_weighted'] = safe_float(result.desktop_duration_weighted)
    totals['mobile_duration_weighted'] = safe_float(result.mobile_duration_weighted)
    totals['duration_weighted'] = safe_float(result.duration_weighted)
    return totals


def build_device_summary(totals: dict[str, int | float]) -> DeviceSummary:
    """Build aggregate device summary.
    Args:
        totals (dict[str, int | float]): Aggregate device totals."""
    visits_total = int(totals['visits_total'])
    desktop_visits = int(totals['desktop_visits'])
    mobile_visits = int(totals['mobile_visits'])
    dominant_device = None
    if visits_total > 0:
        dominant_device = 'desktop' if desktop_visits >= mobile_visits else 'mobile'
    return DeviceSummary(
        visits_total=visits_total,
        desktop_visits=desktop_visits,
        mobile_visits=mobile_visits,
        desktop_share=divide_values(desktop_visits, visits_total),
        mobile_share=divide_values(mobile_visits, visits_total),
        unique_total=int(totals['unique_total']),
        desktop_unique=int(totals['desktop_unique']),
        mobile_unique=int(totals['mobile_unique']),
        dominant_device=dominant_device,
    )


def build_device_quality(totals: dict[str, int | float]) -> DeviceQuality:
    """Build aggregate device quality.
    Args:
        totals (dict[str, int | float]): Aggregate device totals."""
    desktop_visits = int(totals['desktop_visits'])
    mobile_visits = int(totals['mobile_visits'])
    visits_total = int(totals['visits_total'])
    desktop_bounce_rate = divide_values(
        int(totals['desktop_bounce']),
        int(totals['desktop_bounce']) + int(totals['desktop_no_bounce']),
    )
    mobile_bounce_rate = divide_values(
        int(totals['mobile_bounce']),
        int(totals['mobile_bounce']) + int(totals['mobile_no_bounce']),
    )
    desktop_duration = divide_values(float(totals['desktop_duration_weighted']), desktop_visits)
    mobile_duration = divide_values(float(totals['mobile_duration_weighted']), mobile_visits)
    duration_total = divide_values(float(totals['duration_weighted']), visits_total)
    desktop_quality = calculate_quality(desktop_duration, desktop_bounce_rate) if desktop_visits > 0 else 0.0
    mobile_quality = calculate_quality(mobile_duration, mobile_bounce_rate) if mobile_visits > 0 else 0.0
    return DeviceQuality(
        desktop_bounce_rate=desktop_bounce_rate,
        mobile_bounce_rate=mobile_bounce_rate,
        desktop_duration=desktop_duration,
        mobile_duration=mobile_duration,
        duration_total=duration_total,
        duration_gap=desktop_duration - mobile_duration,
        desktop_quality_index=desktop_quality,
        mobile_quality_index=mobile_quality,
        quality_gap=desktop_quality - mobile_quality,
    )


def build_bounce_split(totals: dict[str, int | float]) -> DeviceBounceSplit:
    """Build aggregate bounce split.
    Args:
        totals (dict[str, int | float]): Aggregate device totals."""
    total_bounce = int(totals['total_bounce'])
    total_no_bounce = int(totals['total_no_bounce'])
    return DeviceBounceSplit(
        desktop_bounce=int(totals['desktop_bounce']),
        desktop_no_bounce=int(totals['desktop_no_bounce']),
        mobile_bounce=int(totals['mobile_bounce']),
        mobile_no_bounce=int(totals['mobile_no_bounce']),
        total_bounce=total_bounce,
        total_no_bounce=total_no_bounce,
        total_bounce_rate=divide_values(total_bounce, total_bounce + total_no_bounce),
    )


def fetch_device_trend(session: Session, filters: list[Any]) -> list[DeviceTrendPoint]:
    """Fetch daily device trend.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions."""
    rows = session.execute(
        select(
            FactDeviceTrendsDaily.date.label('date'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_devices), 0).label('visits_total'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_desktop), 0).label('desktop_visits'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_mobile), 0).label('mobile_visits'),
        )
        .where(*filters)
        .group_by(FactDeviceTrendsDaily.date)
        .order_by(FactDeviceTrendsDaily.date)
    ).all()
    return [
        DeviceTrendPoint(
            date=row.date,
            desktop_visits=safe_int(row.desktop_visits),
            mobile_visits=safe_int(row.mobile_visits),
            desktop_share=divide_values(safe_int(row.desktop_visits), safe_int(row.visits_total)),
            mobile_share=divide_values(safe_int(row.mobile_visits), safe_int(row.visits_total)),
        )
        for row in rows
    ]


def classify_company_signal(
    desktop_share: float,
    mobile_share: float,
    desktop_quality: float,
    mobile_quality: float,
) -> str:
    """Classify company device quality.
    Args:
        desktop_share (float): Company desktop traffic share.
        mobile_share (float): Company mobile traffic share.
        desktop_quality (float): Company desktop quality index.
        mobile_quality (float): Company mobile quality index."""
    quality_gap = desktop_quality - mobile_quality
    if mobile_share >= 0.40 and quality_gap >= 0.15:
        return 'mobile_quality_gap'
    if quality_gap >= 0.15:
        return 'desktop_quality_advantage'
    if mobile_quality >= desktop_quality and mobile_share >= 0.50:
        return 'mobile_strength'
    if abs(quality_gap) < 0.10:
        return 'balanced_device_quality'
    return 'mixed_device_quality'


def fetch_company_quality(
    session: Session,
    filters: list[Any],
    limit: int,
) -> list[CompetitorDeviceQuality]:
    """Fetch company device quality.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        limit (int): Result row limit."""
    rows = session.execute(
        select(
            FactDeviceTrendsDaily.company_id.label('company_id'),
            DimCompany.name.label('company'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_devices), 0).label('visits_total'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_desktop), 0).label('desktop_visits'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.visits_mobile), 0).label('mobile_visits'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.desktop_bounce), 0).label('desktop_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.desktop_no_bounce), 0).label('desktop_no_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.mobile_bounce), 0).label('mobile_bounce'),
            func.coalesce(func.sum(FactDeviceTrendsDaily.mobile_no_bounce), 0).label('mobile_no_bounce'),
            func.coalesce(
                func.sum(FactDeviceTrendsDaily.duration_desktop * FactDeviceTrendsDaily.visits_desktop),
                0,
            ).label('desktop_duration_weighted'),
            func.coalesce(
                func.sum(FactDeviceTrendsDaily.duration_mobile * FactDeviceTrendsDaily.visits_mobile),
                0,
            ).label('mobile_duration_weighted'),
        )
        .join(DimCompany, FactDeviceTrendsDaily.company_id == DimCompany.id)
        .where(*filters)
        .group_by(FactDeviceTrendsDaily.company_id, DimCompany.name)
        .order_by(func.sum(FactDeviceTrendsDaily.visits_devices).desc())
        .limit(limit)
    ).all()
    quality_rows: list[CompetitorDeviceQuality] = []
    for row in rows:
        visits_total = safe_int(row.visits_total)
        desktop_visits = safe_int(row.desktop_visits)
        mobile_visits = safe_int(row.mobile_visits)
        desktop_share = divide_values(desktop_visits, visits_total)
        mobile_share = divide_values(mobile_visits, visits_total)
        desktop_bounce_rate = divide_values(
            safe_int(row.desktop_bounce),
            safe_int(row.desktop_bounce) + safe_int(row.desktop_no_bounce),
        )
        mobile_bounce_rate = divide_values(
            safe_int(row.mobile_bounce),
            safe_int(row.mobile_bounce) + safe_int(row.mobile_no_bounce),
        )
        desktop_duration = divide_values(safe_float(row.desktop_duration_weighted), desktop_visits)
        mobile_duration = divide_values(safe_float(row.mobile_duration_weighted), mobile_visits)
        desktop_quality = calculate_quality(desktop_duration, desktop_bounce_rate) if desktop_visits > 0 else 0.0
        mobile_quality = calculate_quality(mobile_duration, mobile_bounce_rate) if mobile_visits > 0 else 0.0
        quality_rows.append(
            CompetitorDeviceQuality(
                company_id=safe_int(row.company_id),
                company=row.company,
                desktop_visits=desktop_visits,
                mobile_visits=mobile_visits,
                desktop_share=desktop_share,
                mobile_share=mobile_share,
                desktop_bounce_rate=desktop_bounce_rate,
                mobile_bounce_rate=mobile_bounce_rate,
                desktop_duration=desktop_duration,
                mobile_duration=mobile_duration,
                desktop_quality_index=desktop_quality,
                mobile_quality_index=mobile_quality,
                quality_gap=desktop_quality - mobile_quality,
                signal=classify_company_signal(
                    desktop_share,
                    mobile_share,
                    desktop_quality,
                    mobile_quality,
                ),
            )
        )
    return quality_rows


def build_device_signals(
    totals: dict[str, int | float],
    summary: DeviceSummary,
    quality: DeviceQuality,
) -> list[DeviceSignal]:
    """Build neutral device signals.
    Args:
        totals (dict[str, int | float]): Aggregate device totals.
        summary (DeviceSummary): Aggregate device summary.
        quality (DeviceQuality): Aggregate device quality."""
    signals: list[DeviceSignal] = []
    first_mobile = int(totals['first_mobile'])
    second_mobile = int(totals['second_mobile'])
    if first_mobile == 0 and second_mobile > 0:
        signals.append(
            DeviceSignal(
                type='mobile_new_activity',
                severity='low',
                message='Mobile traffic appears in the second half of the selected period.',
            )
        )
    elif divide_values(second_mobile - first_mobile, first_mobile) >= 0.10 and quality.quality_gap >= 0.15:
        signals.append(
            DeviceSignal(
                type='mobile_growth_low_quality',
                severity='medium',
                message='Mobile traffic is growing, while mobile engagement quality remains weaker than desktop.',
            )
        )
    if summary.desktop_share >= 0.45 and quality.quality_gap >= 0.15:
        signals.append(
            DeviceSignal(
                type='desktop_quality_advantage',
                severity='medium',
                message='Desktop shows stronger engagement quality in the selected scope.',
            )
        )
    if quality.mobile_quality_index >= quality.desktop_quality_index and summary.mobile_share >= 0.50:
        signals.append(
            DeviceSignal(
                type='mobile_strength',
                severity='low',
                message='Mobile combines the leading traffic share with comparable or stronger engagement quality.',
            )
        )
    if summary.visits_total > 0 and abs(quality.quality_gap) < 0.10:
        signals.append(
            DeviceSignal(
                type='balanced_device_quality',
                severity='low',
                message='Desktop and mobile engagement quality are broadly balanced in the selected scope.',
            )
        )
    return signals


def build_scope_analytics(
    session: Session,
    filters: list[Any],
    split_date: date | None,
    limit: int,
) -> DeviceScopeAnalytics:
    """Build one device analytics scope.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date | None): Last date in the first period half.
        limit (int): Result row limit."""
    totals = fetch_device_totals(session, filters, split_date)
    summary = build_device_summary(totals)
    quality = build_device_quality(totals)
    return DeviceScopeAnalytics(
        summary=summary,
        quality=quality,
        bounce_split=build_bounce_split(totals),
        device_trend=fetch_device_trend(session, filters),
        competitor_device_quality=fetch_company_quality(session, filters, limit),
        signals=build_device_signals(totals, summary, quality)[:limit],
    )


def get_device_intelligence(
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
) -> DeviceIntelligenceResponse:
    """Get device intelligence analytics.
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
    resolved_date_from, resolved_date_to = read_device_dates(
        session,
        resolved_project_id,
        date_from,
        date_to,
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
    countries = normalize_values(normalized_country)
    country_domains = build_country_scope(
        resolved_project_id,
        resolved_date_from,
        resolved_date_to,
        countries,
    )
    tlds = normalize_values(normalized_tld)
    resolved_limit = normalize_limit(limit)
    combined_scopes = all(
        value.lower() == 'all'
        for value in (
            normalized_company,
            normalized_company_domain,
            normalized_competitors,
            normalized_competitor_domain,
        )
    )

    def read_scope(company_value: str, domain_value: str) -> DeviceScopeAnalytics:
        """Read one separated device scope.
        Args:
            company_value (str): Selected company identifiers.
            domain_value (str): Selected domain values."""
        filters = build_fact_filters(
            FactDeviceTrendsDaily,
            resolved_project_id,
            resolved_date_from,
            resolved_date_to,
            tlds,
            country_domains,
            build_single_scope(FactDeviceTrendsDaily, company_value, domain_value),
        )
        return build_scope_analytics(session, filters, split_date, resolved_limit)

    overall_scope = read_scope('all', 'all') if combined_scopes else None
    company_scope = (
        None
        if combined_scopes or normalized_company.lower() == 'none'
        else read_scope(normalized_company, normalized_company_domain)
    )
    competitor_scope = (
        None
        if combined_scopes or normalized_competitors.lower() == 'none'
        else read_scope(normalized_competitors, normalized_competitor_domain)
    )
    return DeviceIntelligenceResponse(
        filters=DeviceIntelligenceFilters(
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
