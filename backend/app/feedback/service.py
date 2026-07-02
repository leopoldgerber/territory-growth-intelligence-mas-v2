from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.feedback.schemas import (
    ActionExecutionCreate,
    ActionExecutionUpdate,
    ActionResultCreate,
    RecommendationDecisionCreate,
    RecommendationExpectationCreate,
)
from app.models.tables import (
    ActionExecution,
    ActionResult,
    Assumption,
    KnowledgeDocument,
    LearningEvent,
    Recommendation,
    RecommendationDecision,
    RecommendationExpectation,
    ScoringModelReview,
)

DECISIONS = {'accepted', 'rejected', 'deferred', 'needs_more_data'}
REASONS = {
    'unknown',
    'good_fit',
    'budget_constraints',
    'low_confidence',
    'market_risk',
    'strategic_mismatch',
    'missing_data',
    'timing_issue',
    'already_planned',
    'other',
}
ACTION_STATUSES = {'planned', 'running', 'completed', 'cancelled', 'failed'}


class OutcomeComparisonService:
    def compare_outcome(
        self,
        session: Session,
        recommendation: Recommendation,
    ) -> dict[str, Any]:
        """Compare recommendation outcome.
        Args:
            session (Session): Active database session.
            recommendation (Recommendation): Recommendation record."""
        return compare_outcome(session, recommendation)

    def compare_actual(
        self,
        expectations: list[RecommendationExpectation],
        results: list[ActionResult],
    ) -> dict[str, Any]:
        """Compare expected actuals.
        Args:
            expectations (list[RecommendationExpectation]): Recommendation expectations.
            results (list[ActionResult]): Action results."""
        score = calculate_score(results)
        classification = classify_result(score, results)
        notes = extract_notes(expectations, results, classification)
        return {'score': score, 'classification': classification, 'notes': notes}

    def calculate_score(self, results: list[ActionResult]) -> float:
        """Calculate outcome score.
        Args:
            results (list[ActionResult]): Action results."""
        return calculate_score(results)

    def classify_result(self, score: float, results: list[ActionResult]) -> str:
        """Classify result.
        Args:
            score (float): Outcome score.
            results (list[ActionResult]): Action results."""
        return classify_result(score, results)

    def extract_notes(
        self,
        expectations: list[RecommendationExpectation],
        results: list[ActionResult],
        classification: str,
    ) -> list[str]:
        """Extract learning notes.
        Args:
            expectations (list[RecommendationExpectation]): Recommendation expectations.
            results (list[ActionResult]): Action results.
            classification (str): Outcome classification."""
        return extract_notes(expectations, results, classification)


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def read_recommendation(session: Session, project_id: UUID, recommendation_id: UUID) -> Recommendation | None:
    """Read recommendation.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        recommendation_id (UUID): Recommendation identifier."""
    return session.scalar(
        select(Recommendation).where(
            Recommendation.project_id == project_id,
            Recommendation.id == recommendation_id,
        )
    )


def create_decision(
    session: Session,
    recommendation: Recommendation,
    request: RecommendationDecisionCreate,
) -> RecommendationDecision:
    """Create recommendation decision.
    Args:
        session (Session): Active database session.
        recommendation (Recommendation): Recommendation record.
        request (RecommendationDecisionCreate): Decision request."""
    if request.decision not in DECISIONS:
        raise ValueError('Unsupported recommendation decision.')
    reason_category = request.reason_category if request.reason_category in REASONS else 'unknown'
    record = RecommendationDecision(
        project_id=recommendation.project_id,
        recommendation_id=recommendation.id,
        mas_run_id=recommendation.mas_run_id,
        user_id=request.user_id,
        decision=request.decision,
        reason_category=reason_category,
        reason_text=request.reason_text,
        expected_action_json=request.expected_action_json,
    )
    session.add(record)
    session.flush()
    apply_decision(recommendation, request.decision, reason_category, request.reason_text)
    learning = decision_learning(session, recommendation, record)
    create_document(session, learning, f'Decision: {recommendation.title}\n{learning.summary}')
    session.commit()
    session.refresh(record)
    return record


def list_decisions(session: Session, recommendation_id: UUID) -> list[RecommendationDecision]:
    """List recommendation decisions.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID): Recommendation identifier."""
    return list(
        session.scalars(
            select(RecommendationDecision)
            .where(RecommendationDecision.recommendation_id == recommendation_id)
            .order_by(RecommendationDecision.created_at.desc())
        ).all()
    )


def apply_decision(
    recommendation: Recommendation,
    decision: str,
    reason_category: str,
    reason_text: str | None,
) -> Recommendation:
    """Apply recommendation decision.
    Args:
        recommendation (Recommendation): Recommendation record.
        decision (str): Decision value.
        reason_category (str): Decision reason category.
        reason_text (str | None): Decision reason text."""
    now = current_time()
    recommendation.user_decision = decision
    recommendation.user_decision_reason = reason_text or reason_category
    if decision == 'accepted':
        recommendation.status = 'accepted'
        recommendation.feedback_status = 'accepted'
        recommendation.accepted_at = now
    elif decision == 'rejected':
        recommendation.status = 'rejected'
        recommendation.feedback_status = 'rejected'
        recommendation.rejected_at = now
    elif decision == 'deferred':
        recommendation.feedback_status = 'not_reviewed'
    else:
        recommendation.feedback_status = 'not_reviewed'
    recommendation.updated_at = now
    return recommendation


def decision_learning(
    session: Session,
    recommendation: Recommendation,
    decision: RecommendationDecision,
) -> LearningEvent:
    """Create decision learning.
    Args:
        session (Session): Active database session.
        recommendation (Recommendation): Recommendation record.
        decision (RecommendationDecision): Recommendation decision."""
    learning_type = 'recommendation_confirmed' if decision.decision == 'accepted' else 'recommendation_rejected'
    summary = (
        f'Recommendation "{recommendation.title}" was {decision.decision}. '
        f'Reason: {decision.reason_category}.'
    )
    record = LearningEvent(
        project_id=recommendation.project_id,
        source_type='recommendation_decision',
        source_record_id=str(decision.id),
        recommendation_id=recommendation.id,
        action_execution_id=None,
        learning_type=learning_type,
        country_id=recommendation.country_id,
        company_id=recommendation.company_id,
        channel=recommendation.channel,
        summary=summary,
        details_json={
            'decision': decision.decision,
            'reason_category': decision.reason_category,
            'reason_text': decision.reason_text,
        },
        impact_area='recommendation',
        confidence='medium',
        status='active',
    )
    session.add(record)
    session.flush()
    recommendation.learning_status = 'learning_ready'
    return record


def create_action(session: Session, project_id: UUID, request: ActionExecutionCreate) -> ActionExecution:
    """Create action execution.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (ActionExecutionCreate): Action execution request."""
    if request.status not in ACTION_STATUSES:
        raise ValueError('Unsupported action status.')
    recommendation = None
    if request.recommendation_id is not None:
        recommendation = read_recommendation(session, project_id, request.recommendation_id)
        if recommendation is None:
            raise ValueError('Recommendation was not found.')
    record = ActionExecution(
        project_id=project_id,
        recommendation_id=request.recommendation_id,
        country_id=request.country_id or (recommendation.country_id if recommendation else None),
        company_id=request.company_id or (recommendation.company_id if recommendation else None),
        strategy_mode=request.strategy_mode or (recommendation.strategy_mode if recommendation else None),
        action_type=request.action_type,
        channel=request.channel or (recommendation.channel if recommendation else None),
        planned_budget=request.planned_budget,
        actual_budget=request.actual_budget,
        currency=request.currency or (recommendation.currency if recommendation else None),
        start_date=request.start_date,
        end_date=request.end_date,
        status=request.status,
        metadata_json=request.metadata_json,
    )
    session.add(record)
    session.flush()
    if recommendation is not None:
        recommendation.feedback_status = (
            'in_progress' if request.status == 'running' else recommendation.feedback_status
        )
        recommendation.linked_campaign_id = record.id
    session.commit()
    session.refresh(record)
    return record


def list_actions(session: Session, project_id: UUID, limit: int, offset: int) -> tuple[list[ActionExecution], int]:
    """List action executions.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    query = (
        select(ActionExecution)
        .where(ActionExecution.project_id == project_id)
        .order_by(ActionExecution.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    total = int(
        session.scalar(
            select(func.count()).select_from(ActionExecution).where(ActionExecution.project_id == project_id)
        )
        or 0
    )
    return list(session.scalars(query).all()), total


def read_action(session: Session, project_id: UUID, action_id: UUID) -> ActionExecution | None:
    """Read action execution.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        action_id (UUID): Action execution identifier."""
    return session.scalar(
        select(ActionExecution).where(
            ActionExecution.project_id == project_id,
            ActionExecution.id == action_id,
        )
    )


def update_action(
    session: Session,
    record: ActionExecution,
    request: ActionExecutionUpdate,
) -> ActionExecution:
    """Update action execution.
    Args:
        session (Session): Active database session.
        record (ActionExecution): Action execution record.
        request (ActionExecutionUpdate): Action execution update."""
    if request.status is not None:
        if request.status not in ACTION_STATUSES:
            raise ValueError('Unsupported action status.')
        record.status = request.status
    if request.actual_budget is not None:
        record.actual_budget = request.actual_budget
    if request.end_date is not None:
        record.end_date = request.end_date
    if request.metadata_json is not None:
        record.metadata_json = request.metadata_json
    record.updated_at = current_time()
    session.commit()
    session.refresh(record)
    return record


def create_result(
    session: Session,
    action: ActionExecution,
    request: ActionResultCreate,
) -> ActionResult:
    """Create action result.
    Args:
        session (Session): Active database session.
        action (ActionExecution): Action execution record.
        request (ActionResultCreate): Action result request."""
    record = ActionResult(
        project_id=action.project_id,
        action_execution_id=action.id,
        recommendation_id=action.recommendation_id,
        period_from=request.period_from,
        period_to=request.period_to,
        channel=request.channel or action.channel,
        country_id=request.country_id or action.country_id,
        company_id=request.company_id or action.company_id,
        traffic=request.traffic,
        traffic_growth=request.traffic_growth,
        bounce_rate=request.bounce_rate,
        avg_visit_duration=request.avg_visit_duration,
        pages_per_visit=request.pages_per_visit,
        spend=request.spend,
        conversions=request.conversions,
        revenue=request.revenue,
        cac=request.cac,
        cpa=request.cpa,
        roi=request.roi,
        payback_days=request.payback_days,
        metadata_json=request.metadata_json,
    )
    action.status = 'completed' if action.status == 'running' else action.status
    action.updated_at = current_time()
    update_result_summary(session, action.recommendation_id, record)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_results(session: Session, action_id: UUID) -> list[ActionResult]:
    """List action results.
    Args:
        session (Session): Active database session.
        action_id (UUID): Action execution identifier."""
    return list(
        session.scalars(
            select(ActionResult)
            .where(ActionResult.action_execution_id == action_id)
            .order_by(ActionResult.created_at.desc())
        ).all()
    )


def update_result_summary(
    session: Session,
    recommendation_id: UUID | None,
    result: ActionResult,
) -> Recommendation | None:
    """Update result summary.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID | None): Recommendation identifier.
        result (ActionResult): Action result."""
    if recommendation_id is None:
        return None
    recommendation = session.get(Recommendation, recommendation_id)
    if recommendation is None:
        return None
    recommendation.actual_outcome_json = result_payload(result)
    recommendation.feedback_status = 'outcome_recorded'
    recommendation.updated_at = current_time()
    return recommendation


def create_expectation(
    session: Session,
    recommendation: Recommendation,
    request: RecommendationExpectationCreate,
) -> RecommendationExpectation:
    """Create recommendation expectation.
    Args:
        session (Session): Active database session.
        recommendation (Recommendation): Recommendation record.
        request (RecommendationExpectationCreate): Expectation request."""
    record = RecommendationExpectation(
        project_id=recommendation.project_id,
        recommendation_id=recommendation.id,
        mas_run_id=recommendation.mas_run_id,
        expected_direction=request.expected_direction,
        expected_metric=request.expected_metric,
        expected_value_min=request.expected_value_min,
        expected_value_max=request.expected_value_max,
        expected_time_window_days=request.expected_time_window_days,
        assumptions_json=request.assumptions_json,
        confidence=request.confidence,
    )
    recommendation.expected_outcome_json = {
        'expected_direction': request.expected_direction,
        'expected_metric': request.expected_metric,
        'assumptions': request.assumptions_json,
    }
    session.add(record)
    create_assumptions(session, recommendation, record)
    session.commit()
    session.refresh(record)
    return record


def list_expectations(session: Session, recommendation_id: UUID) -> list[RecommendationExpectation]:
    """List expectations.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID): Recommendation identifier."""
    return list(
        session.scalars(
            select(RecommendationExpectation)
            .where(RecommendationExpectation.recommendation_id == recommendation_id)
            .order_by(RecommendationExpectation.created_at.desc())
        ).all()
    )


def create_assumptions(
    session: Session,
    recommendation: Recommendation,
    expectation: RecommendationExpectation,
) -> list[Assumption]:
    """Create assumptions.
    Args:
        session (Session): Active database session.
        recommendation (Recommendation): Recommendation record.
        expectation (RecommendationExpectation): Expectation record."""
    statements = read_statements(expectation.assumptions_json)
    if not statements:
        statements = [recommendation.description]
    records: list[Assumption] = []
    for statement in statements:
        record = Assumption(
            project_id=recommendation.project_id,
            source_type='recommendation_expectation',
            source_record_id=str(expectation.id),
            recommendation_id=recommendation.id,
            mas_run_id=recommendation.mas_run_id,
            assumption_type=expectation.expected_metric,
            statement=statement,
            evidence_refs_json=[],
            confidence=expectation.confidence,
            status='active',
        )
        session.add(record)
        records.append(record)
    return records


def compare_outcome(session: Session, recommendation: Recommendation) -> dict[str, Any]:
    """Compare recommendation outcome.
    Args:
        session (Session): Active database session.
        recommendation (Recommendation): Recommendation record."""
    expectations = list_expectations(session, recommendation.id)
    actions = read_actions(session, recommendation.id)
    results = read_results(session, recommendation.id)
    service = OutcomeComparisonService()
    comparison = service.compare_actual(expectations, results)
    learning = outcome_learning(session, recommendation, actions, results, comparison)
    assumptions_updated = update_assumptions(session, recommendation.id, comparison['classification'])
    model_review = create_review(session, learning, comparison['classification'])
    recommendation.learning_status = 'learning_ready'
    if comparison['classification'] in {'confirmed', 'partially_confirmed'}:
        recommendation.feedback_status = 'learning_ready'
    if comparison['classification'] == 'contradicted':
        recommendation.feedback_status = 'learning_ready'
    create_document(session, learning, build_learning_text(learning, comparison['notes']))
    session.commit()
    session.refresh(learning)
    if model_review is not None:
        session.refresh(model_review)
    return {
        'classification': comparison['classification'],
        'outcome_score': comparison['score'],
        'learning_event': learning,
        'notes': comparison['notes'],
        'assumptions_updated': assumptions_updated,
        'model_review': model_review,
    }


def outcome_learning(
    session: Session,
    recommendation: Recommendation,
    actions: list[ActionExecution],
    results: list[ActionResult],
    comparison: dict[str, Any],
) -> LearningEvent:
    """Create outcome learning.
    Args:
        session (Session): Active database session.
        recommendation (Recommendation): Recommendation record.
        actions (list[ActionExecution]): Action executions.
        results (list[ActionResult]): Action results.
        comparison (dict[str, Any]): Outcome comparison."""
    classification = comparison['classification']
    learning_type = learning_type_for(classification)
    summary = f'Recommendation "{recommendation.title}" outcome is {classification}.'
    record = LearningEvent(
        project_id=recommendation.project_id,
        source_type='outcome_comparison',
        source_record_id=str(recommendation.id),
        recommendation_id=recommendation.id,
        action_execution_id=actions[0].id if actions else None,
        learning_type=learning_type,
        country_id=recommendation.country_id,
        company_id=recommendation.company_id,
        channel=recommendation.channel,
        summary=summary,
        details_json={
            'classification': classification,
            'outcome_score': comparison['score'],
            'notes': comparison['notes'],
            'results_count': len(results),
        },
        impact_area=impact_area_for(recommendation),
        confidence='medium' if results else 'low',
        status='active',
    )
    session.add(record)
    session.flush()
    return record


def create_review(
    session: Session,
    learning: LearningEvent,
    classification: str,
) -> ScoringModelReview | None:
    """Create model review.
    Args:
        session (Session): Active database session.
        learning (LearningEvent): Learning event.
        classification (str): Outcome classification."""
    if classification not in {'contradicted', 'partially_confirmed'}:
        return None
    record = ScoringModelReview(
        project_id=learning.project_id,
        source_learning_event_id=learning.id,
        model_name='opportunity_score',
        current_version='v1',
        proposed_version='v1_review',
        proposed_changes_json={
            'review_needed': True,
            'impact_area': learning.impact_area,
            'classification': classification,
        },
        reason=learning.summary,
        status='proposed',
    )
    session.add(record)
    session.flush()
    return record


def create_document(session: Session, learning: LearningEvent, content: str) -> KnowledgeDocument:
    """Create feedback document.
    Args:
        session (Session): Active database session.
        learning (LearningEvent): Learning event.
        content (str): Document content."""
    existing = session.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.project_id == learning.project_id,
            KnowledgeDocument.source_type == 'feedback_learning_event',
            KnowledgeDocument.source_record_id == str(learning.id),
        )
    )
    if existing is not None:
        return existing
    record = KnowledgeDocument(
        project_id=learning.project_id,
        document_type='feedback_learning',
        source_type='feedback_learning_event',
        source_record_id=str(learning.id),
        title=f'Feedback learning: {learning.learning_type}',
        content=content,
        metadata_json={
            'recommendation_id': str(learning.recommendation_id) if learning.recommendation_id else None,
            'learning_type': learning.learning_type,
            'impact_area': learning.impact_area,
        },
        status='ready',
        version='v1',
    )
    session.add(record)
    session.flush()
    return record


def list_learning(session: Session, project_id: UUID, limit: int, offset: int) -> tuple[list[LearningEvent], int]:
    """List learning events.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    query = (
        select(LearningEvent)
        .where(LearningEvent.project_id == project_id)
        .order_by(LearningEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    total = int(
        session.scalar(
            select(func.count()).select_from(LearningEvent).where(LearningEvent.project_id == project_id)
        )
        or 0
    )
    return list(session.scalars(query).all()), total


def list_reviews(session: Session, project_id: UUID, limit: int, offset: int) -> tuple[list[ScoringModelReview], int]:
    """List model reviews.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        limit (int): Result limit.
        offset (int): Result offset."""
    query = (
        select(ScoringModelReview)
        .where(ScoringModelReview.project_id == project_id)
        .order_by(ScoringModelReview.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    total = int(
        session.scalar(
            select(func.count()).select_from(ScoringModelReview).where(ScoringModelReview.project_id == project_id)
        )
        or 0
    )
    return list(session.scalars(query).all()), total


def read_actions(session: Session, recommendation_id: UUID) -> list[ActionExecution]:
    """Read recommendation actions.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID): Recommendation identifier."""
    return list(
        session.scalars(
            select(ActionExecution).where(ActionExecution.recommendation_id == recommendation_id)
        ).all()
    )


def read_results(session: Session, recommendation_id: UUID) -> list[ActionResult]:
    """Read recommendation results.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID): Recommendation identifier."""
    return list(session.scalars(select(ActionResult).where(ActionResult.recommendation_id == recommendation_id)).all())


def calculate_score(results: list[ActionResult]) -> float:
    """Calculate outcome score.
    Args:
        results (list[ActionResult]): Action results."""
    if not results:
        return 0.0
    values: list[float] = []
    for result in results:
        if result.traffic_growth is not None:
            values.append(clamp(float(result.traffic_growth), -1.0, 1.0))
        if result.bounce_rate is not None:
            values.append(0.3 - clamp(float(result.bounce_rate), 0.0, 1.0))
        if result.roi is not None:
            values.append(clamp(float(result.roi), -1.0, 1.0))
    if not values:
        return 0.0
    return sum(values) / len(values)


def classify_result(score: float, results: list[ActionResult]) -> str:
    """Classify outcome result.
    Args:
        score (float): Outcome score.
        results (list[ActionResult]): Action results."""
    if not results:
        return 'insufficient_data'
    if score >= 0.35:
        return 'confirmed'
    if score >= 0.10:
        return 'partially_confirmed'
    if score >= -0.10:
        return 'neutral'
    return 'contradicted'


def extract_notes(
    expectations: list[RecommendationExpectation],
    results: list[ActionResult],
    classification: str,
) -> list[str]:
    """Extract learning notes.
    Args:
        expectations (list[RecommendationExpectation]): Recommendation expectations.
        results (list[ActionResult]): Action results.
        classification (str): Outcome classification."""
    notes = [f'Outcome classification: {classification}.']
    if expectations:
        metrics = ', '.join(sorted({expectation.expected_metric for expectation in expectations}))
        notes.append(f'Expected metrics reviewed: {metrics}.')
    if results:
        notes.append(f'Actual result records reviewed: {len(results)}.')
    if any(result.spend is not None for result in results):
        notes.append('Financial outcome data is partially available.')
    else:
        notes.append('Financial outcome data is not available yet.')
    return notes


def update_assumptions(session: Session, recommendation_id: UUID, classification: str) -> int:
    """Update assumptions.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID): Recommendation identifier.
        classification (str): Outcome classification."""
    records = list(session.scalars(select(Assumption).where(Assumption.recommendation_id == recommendation_id)).all())
    status = assumption_status(classification)
    for record in records:
        record.status = status
        record.updated_at = current_time()
    return len(records)


def assumption_status(classification: str) -> str:
    """Build assumption status.
    Args:
        classification (str): Outcome classification."""
    if classification == 'confirmed':
        return 'confirmed'
    if classification == 'partially_confirmed':
        return 'weakened'
    if classification == 'contradicted':
        return 'contradicted'
    return 'active'


def learning_type_for(classification: str) -> str:
    """Build learning type.
    Args:
        classification (str): Outcome classification."""
    if classification == 'confirmed':
        return 'recommendation_confirmed'
    if classification == 'contradicted':
        return 'assumption_contradicted'
    if classification == 'partially_confirmed':
        return 'score_factor_review_needed'
    return 'recommendation_rejected'


def impact_area_for(recommendation: Recommendation) -> str:
    """Build impact area.
    Args:
        recommendation (Recommendation): Recommendation record."""
    if recommendation.channel:
        return 'channel'
    if recommendation.recommendation_type and 'budget' in recommendation.recommendation_type:
        return 'budget'
    return 'scoring'


def read_statements(data: dict[str, Any]) -> list[str]:
    """Read assumption statements.
    Args:
        data (dict[str, Any]): Assumptions data."""
    value = data.get('statements') or data.get('assumptions')
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def result_payload(result: ActionResult) -> dict[str, Any]:
    """Build result payload.
    Args:
        result (ActionResult): Action result."""
    return {
        'traffic': result.traffic,
        'traffic_growth': decimal_value(result.traffic_growth),
        'bounce_rate': decimal_value(result.bounce_rate),
        'avg_visit_duration': decimal_value(result.avg_visit_duration),
        'pages_per_visit': decimal_value(result.pages_per_visit),
        'spend': decimal_value(result.spend),
        'conversions': decimal_value(result.conversions),
        'revenue': decimal_value(result.revenue),
        'roi': decimal_value(result.roi),
    }


def build_learning_text(learning: LearningEvent, notes: list[str]) -> str:
    """Build learning text.
    Args:
        learning (LearningEvent): Learning event.
        notes (list[str]): Learning notes."""
    return '\n'.join([learning.summary, *notes])


def decimal_value(value: Decimal | None) -> float | None:
    """Convert decimal value.
    Args:
        value (Decimal | None): Decimal value."""
    if value is None:
        return None
    return float(value)


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp numeric value.
    Args:
        value (float): Source value.
        min_value (float): Minimum value.
        max_value (float): Maximum value."""
    return max(min_value, min(max_value, value))
