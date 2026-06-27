from __future__ import annotations

from sqlalchemy.orm import Session

from app.analytics.scoring.service import recalculate_scores
from app.analytics.signals.service import recalculate_signals
from app.reports.budget_strategy.schemas import (
    BudgetStrategyGenerateRequest,
    DependencyItemStatus,
    DependencyStatus,
)
from app.schemas.analytics import OpportunityScoreRecalculateRequest, RecalculateSignalsRequest


def prepare_dependencies(
    session: Session,
    default_project_id: str,
    request: BudgetStrategyGenerateRequest,
    scope: str,
    context_hash: str,
    context_json: dict[str, object],
) -> DependencyStatus:
    """Prepare report analytical dependencies.
    Args:
        session (Session): Active database session.
        default_project_id (str): Default project identifier.
        request (BudgetStrategyGenerateRequest): Strategy request.
        scope (str): Analytical scope.
        context_hash (str): Strategy context hash.
        context_json (dict[str, object]): Strategy context JSON."""
    contexts = [scope, request.strategy_mode]
    if not request.auto_prepare_dependencies:
        skipped = DependencyItemStatus(required=True, status='skipped', contexts=contexts)
        return DependencyStatus(signals=skipped, opportunity_score=skipped, fallbacks_used=['dependencies_skipped'])
    signal_status = DependencyItemStatus(required=True, status='recalculated', contexts=contexts)
    score_status = DependencyItemStatus(required=True, status='recalculated', contexts=contexts)
    fallbacks_used: list[str] = []
    try:
        recalculate_signals(
            session,
            default_project_id,
            RecalculateSignalsRequest(
                date_from=request.date_from,
                date_to=request.date_to,
                country=request.country,
                tld=request.tld,
                company=request.company,
                company_domain=request.company_domain,
                competitors=request.competitors,
                competitor_domain=request.competitor_domain,
                calculation_version=request.calculation_version,
                context_hash=context_hash,
                context_json=context_json,
            ),
        )
    except Exception as error:
        session.rollback()
        signal_status = DependencyItemStatus(
            required=True,
            status='failed',
            contexts=contexts,
            message=str(error),
        )
        fallbacks_used.append('signals')
    try:
        recalculate_scores(
            session,
            default_project_id,
            OpportunityScoreRecalculateRequest(
                date_from=request.date_from,
                date_to=request.date_to,
                country=request.country,
                tld=request.tld,
                company=request.company,
                company_domain=request.company_domain,
                competitors=request.competitors,
                competitor_domain=request.competitor_domain,
                calculation_version=request.calculation_version,
                context_hash=context_hash,
                context_json=context_json,
            ),
        )
    except Exception as error:
        session.rollback()
        score_status = DependencyItemStatus(
            required=True,
            status='failed',
            contexts=contexts,
            message=str(error),
        )
        fallbacks_used.append('opportunity_score')
    return DependencyStatus(
        signals=signal_status,
        opportunity_score=score_status,
        fallbacks_used=fallbacks_used,
    )
