from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.analytics.country_intelligence import (
    normalize_limit,
    normalize_text,
    normalize_values,
    resolve_project,
    safe_float,
)
from app.analytics.scoring.calculators import build_candidate
from app.analytics.scoring.repository import (
    delete_scores,
    fetch_country_metrics,
    fetch_score_signals,
    insert_scores,
    select_scores,
)
from app.analytics.scoring.schemas import ScoreCandidate
from app.schemas.analytics import (
    OpportunityScoreItem,
    OpportunityScoreRecalculateRequest,
    OpportunityScoreRecalculateResponse,
    OpportunityScoresResponse,
    OpportunityScoreSummary,
)


def read_scope_values(request: OpportunityScoreRecalculateRequest) -> list[tuple[str, str, str]]:
    """Read scoring scope definitions.
    Args:
        request (OpportunityScoreRecalculateRequest): Scoring request."""
    combined_scopes = all(
        value.lower() == 'all'
        for value in (
            request.company,
            request.company_domain,
            request.competitors,
            request.competitor_domain,
        )
    )
    if combined_scopes:
        return [('overall', 'all', 'all')]
    scopes: list[tuple[str, str, str]] = []
    if request.company.lower() != 'none':
        scopes.append(('company', request.company, request.company_domain))
    if request.competitors.lower() != 'none':
        scopes.append(('competitor', request.competitors, request.competitor_domain))
    return scopes


def rank_candidates(candidates: list[ScoreCandidate]) -> list[ScoreCandidate]:
    """Rank opportunity candidates within each scope.
    Args:
        candidates (list[ScoreCandidate]): Unranked opportunity candidates."""
    ranked: list[ScoreCandidate] = []
    for scope in ('overall', 'company', 'competitor'):
        scope_candidates = [candidate for candidate in candidates if candidate.scope == scope]
        scope_candidates.sort(
            key=lambda candidate: (
                -candidate.opportunity_score,
                -next(factor.score for factor in candidate.factors if factor.factor == 'market_size'),
                -next(factor.score for factor in candidate.factors if factor.factor == 'growth'),
                -next(factor.score for factor in candidate.factors if factor.factor == 'traffic_quality'),
                candidate.country,
            )
        )
        for rank, candidate in enumerate(scope_candidates, start=1):
            candidate.rank = rank
        ranked.extend(scope_candidates)
    return ranked


def build_scope_scores(
    session: Session,
    project_id: UUID,
    request: OpportunityScoreRecalculateRequest,
    scope: str,
    company_value: str,
    domain_value: str,
) -> list[ScoreCandidate]:
    """Build opportunity candidates for one scope.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (OpportunityScoreRecalculateRequest): Scoring request.
        scope (str): Analytical scope.
        company_value (str): Selected company identifiers.
        domain_value (str): Selected domain values."""
    metrics = fetch_country_metrics(
        session,
        project_id,
        request.date_from,
        request.date_to,
        normalize_values(request.country),
        normalize_values(request.tld),
        company_value,
        domain_value,
    )
    ordered_traffic = sorted({metric.total_traffic for metric in metrics})
    single_country = len(metrics) == 1
    candidates: list[ScoreCandidate] = []
    for metric in metrics:
        percentile = (
            ordered_traffic.index(metric.total_traffic) / (len(ordered_traffic) - 1)
            if len(ordered_traffic) > 1
            else 1.0
        )
        signals = fetch_score_signals(
            session,
            project_id,
            request.date_from,
            request.date_to,
            scope,
            metric.country_id,
            request.calculation_version,
            request.context_hash,
        )
        candidates.append(
            build_candidate(
                metric,
                percentile,
                single_country,
                signals,
                scope,
                request.date_from,
                request.date_to,
                request.calculation_version,
            )
        )
    return candidates


def recalculate_scores(
    session: Session,
    default_project_id: str,
    request: OpportunityScoreRecalculateRequest,
) -> OpportunityScoreRecalculateResponse:
    """Recalculate and persist opportunity scores.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        request (OpportunityScoreRecalculateRequest): Scoring request."""
    if request.date_from > request.date_to:
        raise ValueError('date_from must be before or equal to date_to')
    project_id = resolve_project(None, default_project_id)
    scope_values = read_scope_values(request)
    candidates = rank_candidates(
        [
            candidate
            for scope, company_value, domain_value in scope_values
            for candidate in build_scope_scores(
                session,
                project_id,
                request,
                scope,
                company_value,
                domain_value,
            )
        ]
    )
    signals_missing = any(
        'channel_stability' in candidate.explanation.get('fallbacks_used', []) for candidate in candidates
    )
    note = (
        'Derived signals were not found for this period. Some scoring factors use fallback calculations.'
        if signals_missing
        else None
    )
    try:
        deleted_count = delete_scores(
            session,
            project_id,
            request.date_from,
            request.date_to,
            request.calculation_version,
            request.context_hash,
        )
        records = insert_scores(session, project_id, candidates, request.context_hash, request.context_json)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return OpportunityScoreRecalculateResponse(
        status='success',
        calculation_version=request.calculation_version,
        date_from=request.date_from,
        date_to=request.date_to,
        scores_created=len(records),
        scores_updated=min(deleted_count, len(records)),
        scopes=[scope for scope, _company, _domain in scope_values],
        note=note,
    )


def build_score_item(record: Any, country: str, country_code: str) -> OpportunityScoreItem:
    """Build one public opportunity score item.
    Args:
        record (Any): Persisted opportunity score.
        country (str): Country name.
        country_code (str): Country code."""
    factor_scores = {
        'market_size': safe_float(record.market_size_score),
        'growth': safe_float(record.growth_score),
        'traffic_quality': safe_float(record.traffic_quality_score),
        'competition_level': safe_float(record.competition_level_score),
        'concentration': safe_float(record.concentration_score),
        'channel_stability': safe_float(record.channel_stability_score),
        'entry_risk': safe_float(record.entry_risk_score),
        'position_potential': safe_float(record.position_potential_score),
    }
    return OpportunityScoreItem(
        country_id=record.country_id,
        country=country,
        country_code=country_code,
        scope=record.scope,
        rank=record.rank,
        opportunity_score=safe_float(record.opportunity_score),
        score_category=record.score_category,
        factor_scores=factor_scores,
        strengths=record.strengths or [],
        weaknesses=record.weaknesses or [],
        risks=record.risks or [],
        explanation=record.explanation,
        details=record.details,
        calculation_version=record.calculation_version,
    )


def list_scores(
    session: Session,
    default_project_id: str,
    date_from: date | None,
    date_to: date | None,
    country: str | None,
    scope: str | None,
    score_category: str | None,
    limit: int | None,
) -> OpportunityScoresResponse:
    """List persisted opportunity scores.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        date_from (date | None): Requested start date.
        date_to (date | None): Requested end date.
        country (str | None): Requested country values.
        scope (str | None): Requested analytical scopes.
        score_category (str | None): Requested score categories.
        limit (int | None): Requested row limit."""
    project_id = resolve_project(None, default_project_id)
    rows = select_scores(
        session,
        project_id,
        date_from,
        date_to,
        normalize_values(country),
        None if normalize_text(scope, 'all').lower() == 'all' else normalize_text(scope, 'all'),
        normalize_values(score_category),
        normalize_limit(limit),
    )
    items = [build_score_item(record, country_name, country_code) for record, country_name, country_code in rows]
    note = (
        'Derived signals were not found for this period. Some scoring factors use fallback calculations.'
        if any('channel_stability' in item.explanation.get('fallbacks_used', []) for item in items)
        else None
    )
    return OpportunityScoresResponse(items=items, note=note)


def summarize_scores(items: list[OpportunityScoreItem]) -> OpportunityScoreSummary:
    """Summarize opportunity score items.
    Args:
        items (list[OpportunityScoreItem]): Persisted score items."""
    if not items:
        return OpportunityScoreSummary(
            total_countries=0,
            average_score=0.0,
            top_country=None,
            top_score=0.0,
            by_category={},
        )
    top_item = max(items, key=lambda item: item.opportunity_score)
    categories: dict[str, int] = {}
    for item in items:
        categories[item.score_category] = categories.get(item.score_category, 0) + 1
    return OpportunityScoreSummary(
        total_countries=len({item.country_id for item in items}),
        average_score=round(sum(item.opportunity_score for item in items) / len(items), 4),
        top_country=top_item.country,
        top_score=top_item.opportunity_score,
        by_category=categories,
    )
