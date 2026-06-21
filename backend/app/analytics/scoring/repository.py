from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import build_single_scope
from app.analytics.country_intelligence import build_filters, divide_values, safe_float, safe_int
from app.analytics.scoring.schemas import CountryMetric, ScoreCandidate
from app.models.tables import DerivedSignal, DimCountry, FactTrafficCountriesDaily, OpportunityScore


def fetch_country_metrics(
    session: Session,
    project_id: UUID,
    date_from: date,
    date_to: date,
    countries: list[str] | None,
    tlds: list[str] | None,
    company_value: str,
    domain_value: str,
) -> list[CountryMetric]:
    """Fetch country-level scoring metrics.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date.
        countries (list[str] | None): Selected country values.
        tlds (list[str] | None): Selected top-level domains.
        company_value (str): Selected company identifiers.
        domain_value (str): Selected domain values."""
    period_days = (date_to - date_from).days + 1
    split_date = date_from + timedelta(days=(period_days - 1) // 2)
    filters = build_filters(project_id, date_from, date_to, countries, None, None, tlds)
    filters.append(build_single_scope(FactTrafficCountriesDaily, company_value, domain_value))
    traffic_value = func.coalesce(FactTrafficCountriesDaily.traffic, 0)
    rows = session.execute(
        select(
            FactTrafficCountriesDaily.country_id.label('country_id'),
            DimCountry.country_name_en.label('country'),
            DimCountry.iso3.label('country_code'),
            func.coalesce(func.sum(traffic_value), 0).label('total_traffic'),
            func.coalesce(
                func.sum(case((FactTrafficCountriesDaily.date <= split_date, traffic_value), else_=0)),
                0,
            ).label('first_traffic'),
            func.coalesce(
                func.sum(case((FactTrafficCountriesDaily.date > split_date, traffic_value), else_=0)),
                0,
            ).label('second_traffic'),
            func.count(func.distinct(FactTrafficCountriesDaily.company_id)).label('active_companies'),
            func.count(func.distinct(FactTrafficCountriesDaily.domain_id)).label('active_domains'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic_bounce), 0).label('bounce'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.traffic_no_bounce), 0).label('no_bounce'),
            func.coalesce(func.sum(FactTrafficCountriesDaily.avg_visit_duration * traffic_value), 0).label(
                'duration_weighted'
            ),
            func.coalesce(func.sum(FactTrafficCountriesDaily.pages_per_visit * traffic_value), 0).label(
                'pages_weighted'
            ),
        )
        .join(DimCountry, FactTrafficCountriesDaily.country_id == DimCountry.id)
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.country_id, DimCountry.country_name_en, DimCountry.iso3)
        .having(func.sum(traffic_value) > 0)
    ).all()
    company_rows = session.execute(
        select(
            FactTrafficCountriesDaily.country_id,
            FactTrafficCountriesDaily.company_id,
            func.coalesce(func.sum(traffic_value), 0).label('traffic'),
        )
        .where(*filters)
        .group_by(FactTrafficCountriesDaily.country_id, FactTrafficCountriesDaily.company_id)
    ).all()
    company_traffic: dict[int, list[int]] = {}
    for row in company_rows:
        company_traffic.setdefault(safe_int(row.country_id), []).append(safe_int(row.traffic))
    metrics: list[CountryMetric] = []
    for row in rows:
        total_traffic = safe_int(row.total_traffic)
        ranked_traffic = sorted(company_traffic.get(safe_int(row.country_id), []), reverse=True)
        bounce = safe_int(row.bounce)
        no_bounce = safe_int(row.no_bounce)
        metrics.append(
            CountryMetric(
                country_id=safe_int(row.country_id),
                country=row.country,
                country_code=row.country_code,
                total_traffic=total_traffic,
                first_traffic=safe_int(row.first_traffic),
                second_traffic=safe_int(row.second_traffic),
                active_companies=safe_int(row.active_companies),
                active_domains=safe_int(row.active_domains),
                top1_share=divide_values(sum(ranked_traffic[:1]), total_traffic),
                top3_share=divide_values(sum(ranked_traffic[:3]), total_traffic),
                bounce_rate=divide_values(bounce, bounce + no_bounce),
                avg_visit_duration=divide_values(safe_float(row.duration_weighted), total_traffic),
                pages_per_visit=divide_values(safe_float(row.pages_weighted), total_traffic),
            )
        )
    if period_days <= 0:
        return []
    return metrics


def fetch_score_signals(
    session: Session,
    project_id: UUID,
    date_from: date,
    date_to: date,
    scope: str,
    country_id: int,
    calculation_version: str,
) -> list[dict[str, Any]]:
    """Fetch applicable derived signals.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date.
        scope (str): Analytical scope.
        country_id (int): Country identifier.
        calculation_version (str): Calculation version."""
    records = session.scalars(
        select(DerivedSignal).where(
            DerivedSignal.project_id == project_id,
            DerivedSignal.date_from == date_from,
            DerivedSignal.date_to == date_to,
            DerivedSignal.scope == scope,
            DerivedSignal.calculation_version == calculation_version,
            or_(DerivedSignal.country_id == country_id, DerivedSignal.country_id.is_(None)),
        )
    ).all()
    return [
        {
            'signal_type': record.signal_type,
            'severity': record.severity,
            'country_id': record.country_id,
        }
        for record in records
    ]


def delete_scores(
    session: Session,
    project_id: UUID,
    date_from: date,
    date_to: date,
    calculation_version: str,
) -> int:
    """Delete existing opportunity scores.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date): Calculation start date.
        date_to (date): Calculation end date.
        calculation_version (str): Calculation version."""
    result = session.execute(
        delete(OpportunityScore).where(
            OpportunityScore.project_id == project_id,
            OpportunityScore.date_from == date_from,
            OpportunityScore.date_to == date_to,
            OpportunityScore.calculation_version == calculation_version,
        )
    )
    return safe_int(result.rowcount)


def build_score_key(project_id: UUID, candidate: ScoreCandidate) -> str:
    """Build deterministic opportunity score key.
    Args:
        project_id (UUID): Project identifier.
        candidate (ScoreCandidate): Opportunity score candidate."""
    return (
        f'{project_id}:{candidate.scope}:{candidate.country_id}:{candidate.date_from}:'
        f'{candidate.date_to}:{candidate.calculation_version}'
    )


def insert_scores(
    session: Session,
    project_id: UUID,
    candidates: list[ScoreCandidate],
) -> list[OpportunityScore]:
    """Insert opportunity score candidates.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        candidates (list[ScoreCandidate]): Ranked score candidates."""
    records: list[OpportunityScore] = []
    for candidate in candidates:
        factor_scores = {factor.factor: factor.score for factor in candidate.factors}
        records.append(
            OpportunityScore(
                project_id=project_id,
                country_id=candidate.country_id,
                scope=candidate.scope,
                score_key=build_score_key(project_id, candidate),
                date_from=candidate.date_from,
                date_to=candidate.date_to,
                opportunity_score=candidate.opportunity_score,
                score_category=candidate.score_category,
                rank=candidate.rank,
                market_size_score=factor_scores['market_size'],
                growth_score=factor_scores['growth'],
                traffic_quality_score=factor_scores['traffic_quality'],
                competition_level_score=factor_scores['competition_level'],
                concentration_score=factor_scores['concentration'],
                channel_stability_score=factor_scores['channel_stability'],
                entry_risk_score=factor_scores['entry_risk'],
                position_potential_score=factor_scores['position_potential'],
                strengths=candidate.strengths,
                weaknesses=candidate.weaknesses,
                risks=candidate.risks,
                explanation=candidate.explanation,
                details=candidate.details,
                calculation_version=candidate.calculation_version,
            )
        )
    session.add_all(records)
    session.flush()
    return records


def select_scores(
    session: Session,
    project_id: UUID,
    date_from: date | None,
    date_to: date | None,
    countries: list[str] | None,
    scope: str | None,
    categories: list[str] | None,
    limit: int,
) -> list[tuple[OpportunityScore, str, str]]:
    """Select persisted opportunity scores.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        countries (list[str] | None): Requested country values.
        scope (str | None): Requested analytical scope.
        categories (list[str] | None): Requested score categories.
        limit (int): Result row limit."""
    filters: list[Any] = [OpportunityScore.project_id == project_id]
    if date_from is not None:
        filters.append(OpportunityScore.date_from == date_from)
    if date_to is not None:
        filters.append(OpportunityScore.date_to == date_to)
    if scope is not None:
        filters.append(OpportunityScore.scope.in_(scope.split(',')) if scope else False)
    if categories is not None:
        filters.append(OpportunityScore.score_category.in_(categories) if categories else False)
    if countries is not None:
        country_values = [value.lower() for value in countries]
        filters.append(
            or_(
                func.lower(DimCountry.iso2).in_(country_values),
                func.lower(DimCountry.iso3).in_(country_values),
                func.lower(DimCountry.country_name_en).in_(country_values),
            )
            if countries
            else False
        )
    return list(
        session.execute(
            select(OpportunityScore, DimCountry.country_name_en, DimCountry.iso3)
            .join(DimCountry, OpportunityScore.country_id == DimCountry.id)
            .where(*filters)
            .order_by(OpportunityScore.scope, OpportunityScore.rank, OpportunityScore.opportunity_score.desc())
            .limit(limit)
        ).all()
    )
