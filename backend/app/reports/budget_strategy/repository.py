from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import safe_float
from app.models.tables import (
    BudgetStrategyReport,
    DerivedSignal,
    DimCompany,
    DimCountry,
    DimDomain,
    FactTrafficCountriesDaily,
    FactTrafficSourcesDaily,
    OpportunityScore,
)
from app.reports.budget_strategy.schemas import BudgetStrategyReportResponse, StrategySource


CHANNELS = ('direct', 'search', 'paid', 'referral', 'social')


def split_filter(value: str) -> list[str] | None:
    """Split one report filter.
    Args:
        value (str): Raw filter value."""
    normalized_value = value.strip().lower()
    if normalized_value == 'all':
        return None
    if normalized_value in {'', 'none'}:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def add_entity_filters(filters: list[Any], company: str, domain: str, tld: str) -> list[Any]:
    """Add company and domain filters.
    Args:
        filters (list[Any]): Existing SQL filters.
        company (str): Company filter value.
        domain (str): Domain filter value.
        tld (str): Top-level domain filter value."""
    company_values = split_filter(company)
    domain_values = split_filter(domain)
    tld_values = split_filter(tld)
    if company_values is not None:
        if not company_values:
            filters.append(False)
        else:
            company_ids = [int(item) for item in company_values if item.isdigit()]
            company_names = [item.lower() for item in company_values if not item.isdigit()]
            company_filters: list[Any] = []
            if company_ids:
                company_filters.append(FactTrafficCountriesDaily.company_id.in_(company_ids))
            if company_names:
                company_filters.append(func.lower(DimCompany.name).in_(company_names))
            filters.append(or_(*company_filters))
    if domain_values is not None:
        if not domain_values:
            filters.append(False)
        else:
            filters.append(DimDomain.domain.in_(domain_values))
    if tld_values is not None:
        if not tld_values:
            filters.append(False)
        else:
            filters.append(DimDomain.tld.in_(tld_values))
    return filters


def resolve_country(session: Session, country: str) -> tuple[int, str, str]:
    """Resolve one required country.
    Args:
        session (Session): Active database session.
        country (str): Country code or name."""
    value = country.strip().lower()
    row = session.execute(
        select(DimCountry.id, DimCountry.country_name_en, DimCountry.iso3).where(
            or_(
                func.lower(DimCountry.iso2) == value,
                func.lower(DimCountry.iso3) == value,
                func.lower(DimCountry.country_name_en) == value,
            )
        )
    ).one_or_none()
    if row is None:
        raise ValueError('country was not found')
    return int(row.id), row.country_name_en, row.iso3


def fetch_strategy_source(
    session: Session,
    project_id: UUID,
    country_id: int,
    date_from: date,
    date_to: date,
    scope: str,
    calculation_version: str,
    context_hash: str | None = None,
) -> StrategySource:
    """Fetch persisted scoring and signal source data.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        country_id (int): Country identifier.
        date_from (date): Report start date.
        date_to (date): Report end date.
        scope (str): Analytical scope.
        calculation_version (str): Calculation version.
        context_hash (str | None): Optional context hash."""
    country = session.execute(
        select(DimCountry.country_name_en, DimCountry.iso3).where(DimCountry.id == country_id)
    ).one()
    score_filters = [
        OpportunityScore.project_id == project_id,
        OpportunityScore.country_id == country_id,
        OpportunityScore.date_from == date_from,
        OpportunityScore.date_to == date_to,
        OpportunityScore.scope == scope,
        OpportunityScore.calculation_version == calculation_version,
    ]
    signal_filters = [
        DerivedSignal.project_id == project_id,
        DerivedSignal.date_from == date_from,
        DerivedSignal.date_to == date_to,
        DerivedSignal.scope == scope,
        DerivedSignal.calculation_version == calculation_version,
        or_(DerivedSignal.country_id == country_id, DerivedSignal.country_id.is_(None)),
    ]
    if context_hash is not None:
        score_filters.append(OpportunityScore.context_hash == context_hash)
        signal_filters.append(DerivedSignal.context_hash == context_hash)
    score = session.scalar(
        select(OpportunityScore)
        .where(*score_filters)
        .order_by(OpportunityScore.updated_at.desc())
    )
    signals = session.scalars(select(DerivedSignal).where(*signal_filters)).all()
    return StrategySource(
        country_id=country_id,
        country=country.country_name_en,
        country_code=country.iso3,
        scope=scope,
        opportunity_score_id=score.id if score else None,
        opportunity_score=safe_float(score.opportunity_score) if score else None,
        opportunity_category=score.score_category if score else None,
        opportunity_strengths=(score.strengths or []) if score else [],
        opportunity_risks=(score.risks or []) if score else [],
        signal_types=sorted({signal.signal_type for signal in signals}),
    )


def has_country_data(
    session: Session,
    project_id: UUID,
    country_id: int,
    date_from: date,
    date_to: date,
    company: str,
    domain: str,
    tld: str,
) -> bool:
    """Check selected country data presence.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        country_id (int): Country identifier.
        date_from (date): Start date.
        date_to (date): End date.
        company (str): Company filter value.
        domain (str): Domain filter value.
        tld (str): Top-level domain filter value."""
    filters: list[Any] = [
        FactTrafficCountriesDaily.project_id == project_id,
        FactTrafficCountriesDaily.country_id == country_id,
        FactTrafficCountriesDaily.date >= date_from,
        FactTrafficCountriesDaily.date <= date_to,
    ]
    add_entity_filters(filters, company, domain, tld)
    value = session.scalar(
        select(func.coalesce(func.sum(FactTrafficCountriesDaily.traffic), 0))
        .join(DimCompany, FactTrafficCountriesDaily.company_id == DimCompany.id)
        .join(DimDomain, FactTrafficCountriesDaily.domain_id == DimDomain.id)
        .where(*filters)
    )
    return int(value or 0) > 0


def has_project_entity(
    session: Session,
    project_id: UUID,
    company: str,
    domain: str,
    tld: str,
) -> bool:
    """Check selected company exists in project.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        company (str): Company filter value.
        domain (str): Domain filter value.
        tld (str): Top-level domain filter value."""
    filters: list[Any] = [FactTrafficCountriesDaily.project_id == project_id]
    add_entity_filters(filters, company, domain, tld)
    value = session.scalar(
        select(func.count(func.distinct(FactTrafficCountriesDaily.company_id)))
        .join(DimCompany, FactTrafficCountriesDaily.company_id == DimCompany.id)
        .join(DimDomain, FactTrafficCountriesDaily.domain_id == DimDomain.id)
        .where(*filters)
    )
    return int(value or 0) > 0


def add_source_filters(filters: list[Any], company: str, domain: str, tld: str) -> list[Any]:
    """Add traffic source entity filters.
    Args:
        filters (list[Any]): Existing SQL filters.
        company (str): Company filter value.
        domain (str): Domain filter value.
        tld (str): Top-level domain filter value."""
    company_values = split_filter(company)
    domain_values = split_filter(domain)
    tld_values = split_filter(tld)
    if company_values is not None:
        if not company_values:
            filters.append(False)
        else:
            company_ids = [int(item) for item in company_values if item.isdigit()]
            company_names = [item.lower() for item in company_values if not item.isdigit()]
            company_filters: list[Any] = []
            if company_ids:
                company_filters.append(FactTrafficSourcesDaily.company_id.in_(company_ids))
            if company_names:
                company_filters.append(func.lower(DimCompany.name).in_(company_names))
            filters.append(or_(*company_filters))
    if domain_values is not None:
        if not domain_values:
            filters.append(False)
        else:
            filters.append(DimDomain.domain.in_(domain_values))
    if tld_values is not None:
        if not tld_values:
            filters.append(False)
        else:
            filters.append(DimDomain.tld.in_(tld_values))
    return filters


def fetch_channel_profile(
    session: Session,
    project_id: UUID,
    date_from: date,
    date_to: date,
    company: str,
    domain: str,
    tld: str,
) -> dict[str, float]:
    """Fetch selected company global channel profile.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date): Start date.
        date_to (date): End date.
        company (str): Company filter value.
        domain (str): Domain filter value.
        tld (str): Top-level domain filter value."""
    filters: list[Any] = [
        FactTrafficSourcesDaily.project_id == project_id,
        FactTrafficSourcesDaily.date >= date_from,
        FactTrafficSourcesDaily.date <= date_to,
    ]
    add_source_filters(filters, company, domain, tld)
    result = session.execute(
        select(
            *[
                func.coalesce(func.sum(getattr(FactTrafficSourcesDaily, channel)), 0).label(channel)
                for channel in CHANNELS
            ]
        )
        .join(DimCompany, FactTrafficSourcesDaily.company_id == DimCompany.id)
        .join(DimDomain, FactTrafficSourcesDaily.domain_id == DimDomain.id)
        .where(*filters)
    ).one()
    totals = {channel: int(getattr(result, channel) or 0) for channel in CHANNELS}
    total_traffic = sum(totals.values())
    if total_traffic <= 0:
        return {channel: 0.0 for channel in CHANNELS}
    return {channel: totals[channel] / total_traffic for channel in CHANNELS}


def build_strategy_key(
    project_id: UUID,
    source: StrategySource,
    date_from: date,
    date_to: date,
    budget_amount: Decimal,
    currency: str,
    calculation_version: str,
    strategy_mode: str,
    context_hash: str,
) -> str:
    """Build deterministic strategy key.
    Args:
        project_id (UUID): Project identifier.
        source (StrategySource): Strategy source identity.
        date_from (date): Report start date.
        date_to (date): Report end date.
        budget_amount (Decimal): Total budget.
        currency (str): Budget currency.
        calculation_version (str): Calculation version.
        strategy_mode (str): Strategy mode.
        context_hash (str): Strategy context hash."""
    budget_key = budget_amount.quantize(Decimal('0.01'))
    return (
        f'{project_id}:{strategy_mode}:{source.scope}:{source.country_id}:{date_from}:{date_to}:'
        f'{budget_key}:{currency}:{calculation_version}:{context_hash}'
    )


def save_report(
    session: Session,
    project_id: UUID,
    source: StrategySource,
    payload: dict[str, Any],
) -> BudgetStrategyReport:
    """Save or replace one budget strategy report.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        source (StrategySource): Strategy source identity.
        payload (dict[str, Any]): Complete report payload."""
    strategy_key = build_strategy_key(
        project_id,
        source,
        payload['date_from'],
        payload['date_to'],
        payload['budget_amount'],
        payload['currency'],
        payload['calculation_version'],
        payload['strategy_mode'],
        payload['context_hash'],
    )
    record = session.scalar(select(BudgetStrategyReport).where(BudgetStrategyReport.strategy_key == strategy_key))
    if record is None:
        record = BudgetStrategyReport(project_id=project_id, country_id=source.country_id, strategy_key=strategy_key)
        session.add(record)
    for field, value in payload.items():
        setattr(record, field, value)
    session.flush()
    session.refresh(record)
    return record


def select_reports(
    session: Session,
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
    country: str | None,
    scope: str | None,
    limit: int,
) -> list[tuple[BudgetStrategyReport, str, str]]:
    """Select saved budget strategy reports.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country value.
        scope (str | None): Requested scope.
        limit (int): Result limit."""
    filters: list[Any] = [BudgetStrategyReport.project_id == project_id]
    if date_from is not None:
        filters.append(BudgetStrategyReport.date_from == date_from)
    if date_to is not None:
        filters.append(BudgetStrategyReport.date_to == date_to)
    if scope and scope.lower() != 'all':
        filters.append(BudgetStrategyReport.scope == scope)
    if country and country.lower() != 'all':
        value = country.lower()
        filters.append(or_(func.lower(DimCountry.iso3) == value, func.lower(DimCountry.country_name_en) == value))
    return list(
        session.execute(
            select(BudgetStrategyReport, DimCountry.country_name_en, DimCountry.iso3)
            .join(DimCountry, BudgetStrategyReport.country_id == DimCountry.id)
            .where(*filters)
            .order_by(BudgetStrategyReport.created_at.desc())
            .limit(limit)
        ).all()
    )


def fetch_report(
    session: Session,
    project_id: UUID,
    report_id: int,
) -> tuple[BudgetStrategyReport, str, str] | None:
    """Fetch one saved budget strategy report.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        report_id (int): Report identifier."""
    return session.execute(
        select(BudgetStrategyReport, DimCountry.country_name_en, DimCountry.iso3)
        .join(DimCountry, BudgetStrategyReport.country_id == DimCountry.id)
        .where(BudgetStrategyReport.project_id == project_id, BudgetStrategyReport.id == report_id)
    ).one_or_none()


def serialize_report(record: BudgetStrategyReport, country: str, country_code: str) -> BudgetStrategyReportResponse:
    """Serialize one saved report.
    Args:
        record (BudgetStrategyReport): Persisted report.
        country (str): Country name.
        country_code (str): Country code."""
    return BudgetStrategyReportResponse(
        id=record.id,
        country=country,
        country_code=country_code,
        date_from=record.date_from,
        date_to=record.date_to,
        budget_amount=safe_float(record.budget_amount),
        currency=record.currency,
        strategy_mode=record.strategy_mode,
        scope=record.scope,
        status=record.status,
        opportunity_score=safe_float(record.opportunity_score) if record.opportunity_score is not None else None,
        recommended_approach=record.recommended_approach,
        allocation=record.allocation,
        channel_roles=record.channel_roles,
        expected_effect=record.expected_effect,
        risks=record.risks,
        explanation=record.explanation,
        dependency_status=record.dependency_status,
        context_hash=record.context_hash,
        context_json=record.context_json,
        source_snapshot=record.source_snapshot,
        calculation_version=record.calculation_version,
        created_at=record.created_at,
    )
