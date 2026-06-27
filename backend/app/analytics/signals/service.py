from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import build_country_scope, build_fact_filters, build_single_scope
from app.analytics.country_intelligence import (
    build_filters,
    normalize_limit,
    normalize_text,
    normalize_values,
    resolve_project,
)
from app.analytics.device_intelligence import get_device_intelligence
from app.analytics.signals.calculators import (
    build_channel_signals,
    build_country_signals,
    build_expansion_signals,
    build_growth_signals,
    build_quality_signals,
)
from app.analytics.signals.repository import (
    build_signal_filters,
    delete_signals,
    fetch_channel_metrics,
    fetch_country_metrics,
    fetch_expansion_metrics,
    fetch_growth_metrics,
    fetch_quality_metric,
    insert_signals,
    select_signals,
    summarize_signals,
)
from app.analytics.signals.schemas import SignalCandidate
from app.models.tables import FactDeviceTrendsDaily, FactTrafficCountriesDaily, FactTrafficSourcesDaily
from app.schemas.analytics import (
    DerivedSignalResponse,
    DerivedSignalSummary,
    RecalculateSignalsRequest,
    RecalculateSignalsResponse,
)


def build_device_candidates(
    session: Session,
    default_project_id: str,
    request: RecalculateSignalsRequest,
    company_value: str,
    domain_value: str,
    scope: str,
) -> list[SignalCandidate]:
    """Build persisted device signal candidates.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        request (RecalculateSignalsRequest): Signal recalculation request.
        company_value (str): Selected company identifiers.
        domain_value (str): Selected domain values.
        scope (str): Analytical scope label."""
    response = get_device_intelligence(
        session=session,
        default_project_id=default_project_id,
        project_id=request.project_id,
        date_from=request.date_from,
        date_to=request.date_to,
        country=request.country,
        tld=request.tld,
        company=company_value,
        company_domain=domain_value,
        competitors='none',
        competitor_domain='all',
        limit=100,
    )
    device_scope = response.company_scope
    if device_scope is None:
        return []
    details = {
        'desktop_share': device_scope.summary.desktop_share,
        'mobile_share': device_scope.summary.mobile_share,
        'desktop_quality_index': device_scope.quality.desktop_quality_index,
        'mobile_quality_index': device_scope.quality.mobile_quality_index,
        'quality_gap': device_scope.quality.quality_gap,
    }
    return [
        SignalCandidate(
            signal_type=signal.type,
            signal_group='device',
            entity_type='device',
            entity_id='selected_scope',
            date_from=request.date_from,
            date_to=request.date_to,
            severity=signal.severity,
            scope=scope,
            value=device_scope.quality.mobile_quality_index,
            baseline_value=device_scope.quality.desktop_quality_index,
            delta_value=-device_scope.quality.quality_gap,
            message=signal.message,
            details=details,
            calculation_version=request.calculation_version,
        )
        for signal in device_scope.signals
    ]


def build_scope_candidates(
    session: Session,
    project_id: UUID,
    default_project_id: str,
    request: RecalculateSignalsRequest,
    company_value: str,
    domain_value: str,
    scope: str,
) -> list[SignalCandidate]:
    """Build derived signal candidates for one scope.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        default_project_id (str): Default project identifier.
        request (RecalculateSignalsRequest): Signal recalculation request.
        company_value (str): Selected company identifiers.
        domain_value (str): Selected domain values.
        scope (str): Analytical scope label."""
    period_days = (request.date_to - request.date_from).days + 1
    split_date = request.date_from + timedelta(days=(period_days - 1) // 2)
    countries = normalize_values(request.country)
    tlds = normalize_values(request.tld)
    traffic_filters = build_filters(
        project_id,
        request.date_from,
        request.date_to,
        countries,
        None,
        None,
        tlds,
    )
    traffic_filters.append(build_single_scope(FactTrafficCountriesDaily, company_value, domain_value))
    country_domains = build_country_scope(project_id, request.date_from, request.date_to, countries)
    source_filters = build_fact_filters(
        FactTrafficSourcesDaily,
        project_id,
        request.date_from,
        request.date_to,
        tlds,
        country_domains,
        build_single_scope(FactTrafficSourcesDaily, company_value, domain_value),
    )
    device_filters = build_fact_filters(
        FactDeviceTrendsDaily,
        project_id,
        request.date_from,
        request.date_to,
        tlds,
        country_domains,
        build_single_scope(FactDeviceTrendsDaily, company_value, domain_value),
    )
    candidates = [
        *build_growth_signals(
            fetch_growth_metrics(session, traffic_filters, split_date, request.date_from, request.date_to),
            request.calculation_version,
        ),
        *build_country_signals(
            fetch_country_metrics(session, traffic_filters, split_date, request.date_from, request.date_to),
            request.calculation_version,
        ),
        *build_channel_signals(
            fetch_channel_metrics(session, source_filters, split_date, request.date_from, request.date_to),
            request.calculation_version,
        ),
        *build_expansion_signals(
            fetch_expansion_metrics(session, traffic_filters, split_date, request.date_from, request.date_to),
            request.calculation_version,
        ),
        *build_quality_signals(
            fetch_quality_metric(session, device_filters, split_date, request.date_from, request.date_to),
            request.calculation_version,
        ),
        *build_device_candidates(
            session,
            default_project_id,
            request,
            company_value,
            domain_value,
            scope,
        ),
    ]
    for candidate in candidates:
        candidate.scope = scope
    return candidates


def recalculate_signals(
    session: Session,
    default_project_id: str,
    request: RecalculateSignalsRequest,
) -> RecalculateSignalsResponse:
    """Recalculate and persist derived signals.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        request (RecalculateSignalsRequest): Signal recalculation request."""
    if request.date_from > request.date_to:
        raise ValueError('date_from must be before or equal to date_to')
    project_id = resolve_project(request.project_id, default_project_id)
    combined_scopes = all(
        value.lower() == 'all'
        for value in (
            request.company,
            request.company_domain,
            request.competitors,
            request.competitor_domain,
        )
    )
    scope_values = [('overall', 'all', 'all')] if combined_scopes else []
    if not combined_scopes and request.company.lower() != 'none':
        scope_values.append(('company', request.company, request.company_domain))
    if not combined_scopes and request.competitors.lower() != 'none':
        scope_values.append(('competitor', request.competitors, request.competitor_domain))
    candidates = [
        candidate
        for scope, company_value, domain_value in scope_values
        for candidate in build_scope_candidates(
            session,
            project_id,
            default_project_id,
            request,
            company_value,
            domain_value,
            scope,
        )
    ]
    try:
        deleted_count = delete_signals(
            session,
            project_id,
            request.date_from,
            request.date_to,
            request.calculation_version,
            request.context_hash,
        )
        records = insert_signals(session, project_id, candidates, request.context_hash, request.context_json)
        session.commit()
        for record in records:
            session.refresh(record)
    except Exception:
        session.rollback()
        raise
    return RecalculateSignalsResponse(
        deleted_count=deleted_count,
        inserted_count=len(records),
        signals=[DerivedSignalResponse.model_validate(record) for record in records],
    )


def list_derived_signals(
    session: Session,
    default_project_id: str,
    project_id: str | None,
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
    limit: int | None,
) -> list[DerivedSignalResponse]:
    """List persisted derived signals.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested calculation start date.
        date_to (date | None): Requested calculation end date.
        signal_group (str | None): Requested signal groups.
        signal_type (str | None): Requested signal types.
        entity_type (str | None): Requested entity types.
        country (str | None): Requested country values.
        company (str | None): Requested company identifiers.
        domain (str | None): Requested domain values.
        severity (str | None): Requested severity values.
        scope (str | None): Requested analytical scope.
        limit (int | None): Requested result limit."""
    resolved_project_id = resolve_project(project_id, default_project_id)
    filters = build_signal_filters(
        resolved_project_id,
        date_from,
        date_to,
        normalize_text(signal_group, 'all'),
        normalize_text(signal_type, 'all'),
        normalize_text(entity_type, 'all'),
        normalize_text(country, 'all'),
        normalize_text(company, 'all'),
        normalize_text(domain, 'all'),
        normalize_text(severity, 'all'),
        normalize_text(scope, 'all'),
    )
    records = select_signals(session, filters, normalize_limit(limit))
    return [DerivedSignalResponse.model_validate(record) for record in records]


def get_signal_summary(
    session: Session,
    default_project_id: str,
    project_id: str | None,
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
) -> DerivedSignalSummary:
    """Summarize persisted derived signals.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        project_id (str | None): Requested project identifier.
        date_from (date | None): Requested calculation start date.
        date_to (date | None): Requested calculation end date.
        signal_group (str | None): Requested signal groups.
        signal_type (str | None): Requested signal types.
        entity_type (str | None): Requested entity types.
        country (str | None): Requested country values.
        company (str | None): Requested company identifiers.
        domain (str | None): Requested domain values.
        severity (str | None): Requested severity values.
        scope (str | None): Requested analytical scope."""
    resolved_project_id = resolve_project(project_id, default_project_id)
    filters = build_signal_filters(
        resolved_project_id,
        date_from,
        date_to,
        normalize_text(signal_group, 'all'),
        normalize_text(signal_type, 'all'),
        normalize_text(entity_type, 'all'),
        normalize_text(country, 'all'),
        normalize_text(company, 'all'),
        normalize_text(domain, 'all'),
        normalize_text(severity, 'all'),
        normalize_text(scope, 'all'),
    )
    total_signals, by_group, by_severity = summarize_signals(session, filters)
    return DerivedSignalSummary(total_signals=total_signals, by_group=by_group, by_severity=by_severity)
