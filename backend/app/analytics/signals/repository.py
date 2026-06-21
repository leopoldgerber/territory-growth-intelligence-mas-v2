from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import divide_values, normalize_ids, normalize_values, safe_float, safe_int
from app.analytics.signals.schemas import SignalCandidate
from app.models.tables import (
    DerivedSignal,
    DimCompany,
    DimCountry,
    DimDomain,
    FactDeviceTrendsDaily,
    FactTrafficCountriesDaily,
    FactTrafficSourcesDaily,
)

CHANNELS = ('direct', 'search', 'paid', 'referral', 'social')


def fetch_growth_level(
    session: Session,
    filters: list[Any],
    split_date: date,
    date_from: date,
    date_to: date,
    entity_type: str,
) -> list[dict[str, Any]]:
    """Fetch entity traffic half metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date): Last date in the first period half.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date.
        entity_type (str): Requested entity granularity."""
    selected_columns: list[Any] = [
        FactTrafficCountriesDaily.country_id.label('country_id'),
        DimCountry.country_name_en.label('country'),
    ]
    group_columns: list[Any] = [FactTrafficCountriesDaily.country_id, DimCountry.country_name_en]
    joins: list[tuple[Any, Any]] = [
        (DimCountry, FactTrafficCountriesDaily.country_id == DimCountry.id),
    ]
    if entity_type == 'country_company':
        selected_columns.extend(
            [
                FactTrafficCountriesDaily.company_id.label('company_id'),
                DimCompany.name.label('company'),
            ]
        )
        group_columns.extend([FactTrafficCountriesDaily.company_id, DimCompany.name])
        joins.append((DimCompany, FactTrafficCountriesDaily.company_id == DimCompany.id))
    if entity_type == 'country_domain':
        selected_columns.extend(
            [
                FactTrafficCountriesDaily.domain_id.label('domain_id'),
                DimDomain.domain.label('domain'),
            ]
        )
        group_columns.extend([FactTrafficCountriesDaily.domain_id, DimDomain.domain])
        joins.append((DimDomain, FactTrafficCountriesDaily.domain_id == DimDomain.id))
    statement = select(
        *selected_columns,
        func.coalesce(
            func.sum(
                case(
                    (FactTrafficCountriesDaily.date <= split_date, FactTrafficCountriesDaily.traffic),
                    else_=0,
                )
            ),
            0,
        ).label('first_traffic'),
        func.coalesce(
            func.sum(
                case(
                    (FactTrafficCountriesDaily.date > split_date, FactTrafficCountriesDaily.traffic),
                    else_=0,
                )
            ),
            0,
        ).label('second_traffic'),
    )
    for table, condition in joins:
        statement = statement.join(table, condition)
    rows = session.execute(statement.where(*filters).group_by(*group_columns)).all()
    metrics: list[dict[str, Any]] = []
    for row in rows:
        company_id = safe_int(row.company_id) if entity_type == 'country_company' else None
        domain_id = safe_int(row.domain_id) if entity_type == 'country_domain' else None
        entity_parts = [str(safe_int(row.country_id))]
        entity_label = row.country
        if company_id is not None:
            entity_parts.append(str(company_id))
            entity_label = f'{row.country} / {row.company}'
        if domain_id is not None:
            entity_parts.append(str(domain_id))
            entity_label = f'{row.country} / {row.domain}'
        metrics.append(
            {
                'entity_type': entity_type,
                'entity_id': ':'.join(entity_parts),
                'entity_label': entity_label,
                'country_id': safe_int(row.country_id),
                'company_id': company_id,
                'domain_id': domain_id,
                'first_traffic': safe_int(row.first_traffic),
                'second_traffic': safe_int(row.second_traffic),
                'date_from': date_from,
                'date_to': date_to,
            }
        )
    return metrics


def fetch_growth_metrics(
    session: Session,
    filters: list[Any],
    split_date: date,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    """Fetch all traffic growth metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date): Last date in the first period half.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date."""
    metrics: list[dict[str, Any]] = []
    for entity_type in ('country', 'country_company', 'country_domain'):
        metrics.extend(fetch_growth_level(session, filters, split_date, date_from, date_to, entity_type))
    return metrics


def fetch_country_metrics(
    session: Session,
    filters: list[Any],
    split_date: date,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    """Fetch country market metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date): Last date in the first period half.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date."""
    country_growth = fetch_growth_level(session, filters, split_date, date_from, date_to, 'country')
    daily_rows = session.execute(
        select(
            FactTrafficCountriesDaily.country_id.label('country_id'),
            FactTrafficCountriesDaily.date.label('date'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('traffic'),
        )
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.country_id, FactTrafficCountriesDaily.date)
    ).all()
    company_rows = session.execute(
        select(
            FactTrafficCountriesDaily.country_id.label('country_id'),
            FactTrafficCountriesDaily.company_id.label('company_id'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0).label('traffic'),
        )
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.country_id, FactTrafficCountriesDaily.company_id)
    ).all()
    daily_map: dict[int, list[int]] = {}
    company_map: dict[int, list[int]] = {}
    for row in daily_rows:
        daily_map.setdefault(safe_int(row.country_id), []).append(safe_int(row.traffic))
    for row in company_rows:
        if safe_int(row.traffic) > 0:
            company_map.setdefault(safe_int(row.country_id), []).append(safe_int(row.traffic))
    metrics: list[dict[str, Any]] = []
    for growth in country_growth:
        company_values = sorted(company_map.get(growth['country_id'], []), reverse=True)
        total_traffic = sum(company_values)
        metrics.append(
            {
                **growth,
                'country': growth['entity_label'],
                'daily_traffic': daily_map.get(growth['country_id'], []),
                'total_traffic': total_traffic,
                'top1_share': divide_values(company_values[0], total_traffic) if company_values else 0.0,
                'top3_share': divide_values(sum(company_values[:3]), total_traffic),
                'active_competitors': len(company_values),
            }
        )
    return metrics


def fetch_channel_metrics(
    session: Session,
    filters: list[Any],
    split_date: date,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    """Fetch channel share half metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date): Last date in the first period half.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date."""
    selected_columns: list[Any] = []
    for channel in CHANNELS:
        column = getattr(FactTrafficSourcesDaily, channel)
        selected_columns.extend(
            [
                func.coalesce(func.sum(case((FactTrafficSourcesDaily.date <= split_date, column), else_=0)), 0).label(
                    f'first_{channel}'
                ),
                func.coalesce(func.sum(case((FactTrafficSourcesDaily.date > split_date, column), else_=0)), 0).label(
                    f'second_{channel}'
                ),
            ]
        )
    result = session.execute(select(*selected_columns).where(*filters)).one()
    first_total = sum(safe_int(getattr(result, f'first_{channel}')) for channel in CHANNELS)
    second_total = sum(safe_int(getattr(result, f'second_{channel}')) for channel in CHANNELS)
    return [
        {
            'channel': channel,
            'first_share': divide_values(safe_int(getattr(result, f'first_{channel}')), first_total),
            'second_share': divide_values(safe_int(getattr(result, f'second_{channel}')), second_total),
            'date_from': date_from,
            'date_to': date_to,
        }
        for channel in CHANNELS
    ]


def fetch_expansion_metrics(
    session: Session,
    filters: list[Any],
    split_date: date,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    """Fetch company territory expansion metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date): Last date in the first period half.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date."""
    rows = session.execute(
        select(
            FactTrafficCountriesDaily.company_id.label('company_id'),
            DimCompany.name.label('company'),
            FactTrafficCountriesDaily.country_id.label('country_id'),
            func.coalesce(
                func.sum(
                    case(
                        (FactTrafficCountriesDaily.date <= split_date, FactTrafficCountriesDaily.traffic),
                        else_=0,
                    )
                ),
                0,
            ).label('first_traffic'),
            func.coalesce(
                func.sum(
                    case(
                        (FactTrafficCountriesDaily.date > split_date, FactTrafficCountriesDaily.traffic),
                        else_=0,
                    )
                ),
                0,
            ).label('second_traffic'),
        )
        .join(DimCompany, FactTrafficCountriesDaily.company_id == DimCompany.id)
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.company_id, DimCompany.name, FactTrafficCountriesDaily.country_id)
    ).all()
    companies: dict[int, dict[str, Any]] = {}
    for row in rows:
        company_id = safe_int(row.company_id)
        metric = companies.setdefault(
            company_id,
            {
                'company_id': company_id,
                'company': row.company,
                'first_traffic': 0,
                'second_traffic': 0,
                'new_country_ids': [],
                'date_from': date_from,
                'date_to': date_to,
            },
        )
        first_traffic = safe_int(row.first_traffic)
        second_traffic = safe_int(row.second_traffic)
        metric['first_traffic'] += first_traffic
        metric['second_traffic'] += second_traffic
        if first_traffic == 0 and second_traffic > 0:
            metric['new_country_ids'].append(safe_int(row.country_id))
    for metric in companies.values():
        metric['new_countries_count'] = len(metric['new_country_ids'])
    return list(companies.values())


def fetch_quality_metric(
    session: Session,
    filters: list[Any],
    split_date: date,
    date_from: date,
    date_to: date,
) -> dict[str, Any]:
    """Fetch traffic quality half metrics.
    Args:
        session (Session): Active database session.
        filters (list[Any]): SQLAlchemy filter expressions.
        split_date (date): Last date in the first period half.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date."""
    first_condition = FactDeviceTrendsDaily.date <= split_date
    second_condition = FactDeviceTrendsDaily.date > split_date
    result = session.execute(
        select(
            func.coalesce(func.sum(case((first_condition, FactDeviceTrendsDaily.all_bounce), else_=0)), 0).label(
                'first_bounce'
            ),
            func.coalesce(
                func.sum(case((first_condition, FactDeviceTrendsDaily.all_no_bounce), else_=0)),
                0,
            ).label('first_no_bounce'),
            func.coalesce(
                func.sum(case((second_condition, FactDeviceTrendsDaily.all_bounce), else_=0)),
                0,
            ).label('second_bounce'),
            func.coalesce(
                func.sum(case((second_condition, FactDeviceTrendsDaily.all_no_bounce), else_=0)),
                0,
            ).label('second_no_bounce'),
            func.coalesce(
                func.sum(
                    case(
                        (
                            first_condition,
                            FactDeviceTrendsDaily.duration_devices * FactDeviceTrendsDaily.visits_devices,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label('first_duration_weighted'),
            func.coalesce(
                func.sum(
                    case(
                        (
                            second_condition,
                            FactDeviceTrendsDaily.duration_devices * FactDeviceTrendsDaily.visits_devices,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label('second_duration_weighted'),
            func.coalesce(func.sum(case((first_condition, FactDeviceTrendsDaily.visits_devices), else_=0)), 0).label(
                'first_visits'
            ),
            func.coalesce(
                func.sum(case((second_condition, FactDeviceTrendsDaily.visits_devices), else_=0)),
                0,
            ).label('second_visits'),
        ).where(*filters)
    ).one()
    first_bounce = safe_int(result.first_bounce)
    first_no_bounce = safe_int(result.first_no_bounce)
    second_bounce = safe_int(result.second_bounce)
    second_no_bounce = safe_int(result.second_no_bounce)
    return {
        'first_bounce_rate': divide_values(first_bounce, first_bounce + first_no_bounce),
        'second_bounce_rate': divide_values(second_bounce, second_bounce + second_no_bounce),
        'first_duration': divide_values(safe_float(result.first_duration_weighted), safe_int(result.first_visits)),
        'second_duration': divide_values(
            safe_float(result.second_duration_weighted),
            safe_int(result.second_visits),
        ),
        'date_from': date_from,
        'date_to': date_to,
    }


def build_signal_key(project_id: UUID, candidate: SignalCandidate) -> str:
    """Build deterministic signal key.
    Args:
        project_id (UUID): Project identifier.
        candidate (SignalCandidate): Derived signal candidate."""
    entity_values = ':'.join(
        str(value or '')
        for value in (
            candidate.entity_id,
            candidate.country_id,
            candidate.company_id,
            candidate.domain_id,
        )
    )
    return (
        f'{project_id}:{candidate.scope}:{candidate.signal_type}:{candidate.entity_type}:{entity_values}:'
        f'{candidate.date_from}:{candidate.date_to}:{candidate.calculation_version}'
    )


def delete_signals(
    session: Session,
    project_id: UUID,
    date_from: date,
    date_to: date,
    calculation_version: str,
) -> int:
    """Delete existing period signals.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date.
        calculation_version (str): Calculation rule version."""
    result = session.execute(
        delete(DerivedSignal).where(
            DerivedSignal.project_id == project_id,
            DerivedSignal.date_from == date_from,
            DerivedSignal.date_to == date_to,
            DerivedSignal.calculation_version == calculation_version,
        )
    )
    return safe_int(result.rowcount)


def insert_signals(
    session: Session,
    project_id: UUID,
    candidates: list[SignalCandidate],
) -> list[DerivedSignal]:
    """Insert derived signal records.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        candidates (list[SignalCandidate]): Derived signal candidates."""
    records = [
        DerivedSignal(
            signal_key=build_signal_key(project_id, candidate),
            project_id=project_id,
            **candidate.model_dump(),
        )
        for candidate in candidates
    ]
    session.add_all(records)
    session.flush()
    return records


def build_signal_filters(
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
    signal_group: str | None,
    signal_type: str | None,
    entity_type: str | None,
    country: str | None,
    company: str | None,
    domain: str | None,
    severity: str | None,
    scope: str | None,
) -> list[Any]:
    """Build stored signal filters.
    Args:
        project_id (UUID): Project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        signal_group (str | None): Requested signal group.
        signal_type (str | None): Requested signal type.
        entity_type (str | None): Requested entity type.
        country (str | None): Requested country values.
        company (str | None): Requested company identifiers.
        domain (str | None): Requested domain values.
        severity (str | None): Requested severity values.
        scope (str | None): Requested analytical scope."""
    filters: list[Any] = [DerivedSignal.project_id == project_id]
    if date_from is not None:
        filters.append(DerivedSignal.date_from == date_from)
    if date_to is not None:
        filters.append(DerivedSignal.date_to == date_to)
    for column, value in (
        (DerivedSignal.signal_group, signal_group),
        (DerivedSignal.signal_type, signal_type),
        (DerivedSignal.entity_type, entity_type),
        (DerivedSignal.severity, severity),
        (DerivedSignal.scope, scope),
    ):
        values = normalize_values(value)
        if values is not None:
            filters.append(column.in_(values) if values else False)
    country_values = normalize_values(country)
    if country_values is not None:
        normalized_countries = [value.lower() for value in country_values]
        country_ids = select(DimCountry.id).where(
            or_(
                func.lower(DimCountry.iso2).in_(normalized_countries),
                func.lower(DimCountry.iso3).in_(normalized_countries),
                func.lower(DimCountry.country_name_en).in_(normalized_countries),
            )
        )
        filters.append(DerivedSignal.country_id.in_(country_ids) if country_values else False)
    company_ids = normalize_ids(company)
    if company_ids is not None:
        filters.append(DerivedSignal.company_id.in_(company_ids) if company_ids else False)
    domain_values = normalize_values(domain)
    if domain_values is not None:
        domain_ids = select(DimDomain.id).where(func.lower(DimDomain.domain).in_([v.lower() for v in domain_values]))
        filters.append(DerivedSignal.domain_id.in_(domain_ids) if domain_values else False)
    return filters


def select_signals(session: Session, filters: list[Any], limit: int) -> list[DerivedSignal]:
    """Select stored derived signals.
    Args:
        session (Session): Active database session.
        filters (list[Any]): Stored signal filter expressions.
        limit (int): Result row limit."""
    statement = select(DerivedSignal).where(*filters).order_by(DerivedSignal.created_at.desc(), DerivedSignal.id.desc())
    return list(session.scalars(statement.limit(limit)).all())


def summarize_signals(session: Session, filters: list[Any]) -> tuple[int, dict[str, int], dict[str, int]]:
    """Summarize stored derived signals.
    Args:
        session (Session): Active database session.
        filters (list[Any]): Stored signal filter expressions."""
    total_signals = safe_int(session.scalar(select(func.count(DerivedSignal.id)).where(*filters)))
    group_rows = session.execute(
        select(DerivedSignal.signal_group, func.count(DerivedSignal.id))
        .where(*filters)
        .group_by(DerivedSignal.signal_group)
    ).all()
    severity_rows = session.execute(
        select(DerivedSignal.severity, func.count(DerivedSignal.id)).where(*filters).group_by(DerivedSignal.severity)
    ).all()
    by_group = {row[0]: safe_int(row[1]) for row in group_rows}
    by_severity = {row[0]: safe_int(row[1]) for row in severity_rows}
    return total_signals, by_group, by_severity
