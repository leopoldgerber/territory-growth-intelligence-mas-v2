from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import resolve_project
from app.core.config import get_settings
from app.core.database import get_session
from app.feedback.schemas import (
    ActionExecutionCreate,
    ActionExecutionListResponse,
    ActionExecutionRead,
    ActionExecutionUpdate,
    ActionResultCreate,
    ActionResultRead,
    LearningEventListResponse,
    ModelReviewListResponse,
    OutcomeComparisonRead,
    RecommendationDecisionCreate,
    RecommendationDecisionRead,
    RecommendationExpectationCreate,
    RecommendationExpectationRead,
)
from app.feedback.service import (
    OutcomeComparisonService,
    create_action,
    create_decision,
    create_expectation,
    create_result,
    list_actions,
    list_decisions,
    list_expectations,
    list_learning,
    list_results,
    list_reviews,
    read_action,
    read_recommendation,
    update_action,
)

router = APIRouter(prefix='/feedback', tags=['feedback'])
SESSION_DEPENDENCY = Depends(get_session)


def project_id() -> UUID:
    """Resolve project identifier.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    return resolve_project(None, settings.default_project_id)


def require_recommendation(session: Session, recommendation_id: UUID) -> object:
    """Require recommendation.
    Args:
        session (Session): Active database session.
        recommendation_id (UUID): Recommendation identifier."""
    record = read_recommendation(session, project_id(), recommendation_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Recommendation was not found')
    return record


def require_action(session: Session, action_id: UUID) -> object:
    """Require action execution.
    Args:
        session (Session): Active database session.
        action_id (UUID): Action execution identifier."""
    record = read_action(session, project_id(), action_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Action execution was not found')
    return record


@router.post('/recommendations/{recommendation_id}/decision', response_model=RecommendationDecisionRead)
def create_recommendation_decision(
    recommendation_id: UUID,
    request: RecommendationDecisionCreate,
    session: Session = SESSION_DEPENDENCY,
) -> RecommendationDecisionRead:
    """Create recommendation decision.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        request (RecommendationDecisionCreate): Decision request.
        session (Session): Active database session."""
    recommendation = require_recommendation(session, recommendation_id)
    try:
        return create_decision(session, recommendation, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get('/recommendations/{recommendation_id}/decisions', response_model=list[RecommendationDecisionRead])
def read_recommendation_decisions(
    recommendation_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> list[RecommendationDecisionRead]:
    """Read recommendation decisions.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        session (Session): Active database session."""
    require_recommendation(session, recommendation_id)
    return list_decisions(session, recommendation_id)


@router.post('/recommendations/{recommendation_id}/expectations', response_model=RecommendationExpectationRead)
def create_recommendation_expectation(
    recommendation_id: UUID,
    request: RecommendationExpectationCreate,
    session: Session = SESSION_DEPENDENCY,
) -> RecommendationExpectationRead:
    """Create recommendation expectation.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        request (RecommendationExpectationCreate): Expectation request.
        session (Session): Active database session."""
    recommendation = require_recommendation(session, recommendation_id)
    return create_expectation(session, recommendation, request)


@router.get('/recommendations/{recommendation_id}/expectations', response_model=list[RecommendationExpectationRead])
def read_recommendation_expectations(
    recommendation_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> list[RecommendationExpectationRead]:
    """Read recommendation expectations.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        session (Session): Active database session."""
    require_recommendation(session, recommendation_id)
    return list_expectations(session, recommendation_id)


@router.post('/recommendations/{recommendation_id}/compare-outcome', response_model=OutcomeComparisonRead)
def compare_recommendation_outcome(
    recommendation_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> OutcomeComparisonRead:
    """Compare recommendation outcome.
    Args:
        recommendation_id (UUID): Recommendation identifier.
        session (Session): Active database session."""
    recommendation = require_recommendation(session, recommendation_id)
    service = OutcomeComparisonService()
    result = service.compare_outcome(session, recommendation)
    return OutcomeComparisonRead(recommendation_id=recommendation_id, **result)


@router.post('/actions', response_model=ActionExecutionRead)
def create_feedback_action(
    request: ActionExecutionCreate,
    session: Session = SESSION_DEPENDENCY,
) -> ActionExecutionRead:
    """Create feedback action.
    Args:
        request (ActionExecutionCreate): Action execution request.
        session (Session): Active database session."""
    try:
        return create_action(session, project_id(), request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get('/actions', response_model=ActionExecutionListResponse)
def read_feedback_actions(
    session: Session = SESSION_DEPENDENCY,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ActionExecutionListResponse:
    """Read feedback actions.
    Args:
        session (Session): Active database session.
        limit (int): Result limit.
        offset (int): Result offset."""
    items, total = list_actions(session, project_id(), limit, offset)
    return ActionExecutionListResponse(items=items, total=total)


@router.get('/actions/{action_id}', response_model=ActionExecutionRead)
def read_feedback_action(action_id: UUID, session: Session = SESSION_DEPENDENCY) -> ActionExecutionRead:
    """Read feedback action.
    Args:
        action_id (UUID): Action execution identifier.
        session (Session): Active database session."""
    return require_action(session, action_id)


@router.patch('/actions/{action_id}', response_model=ActionExecutionRead)
def update_feedback_action(
    action_id: UUID,
    request: ActionExecutionUpdate,
    session: Session = SESSION_DEPENDENCY,
) -> ActionExecutionRead:
    """Update feedback action.
    Args:
        action_id (UUID): Action execution identifier.
        request (ActionExecutionUpdate): Action execution update.
        session (Session): Active database session."""
    record = require_action(session, action_id)
    try:
        return update_action(session, record, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post('/actions/{action_id}/results', response_model=ActionResultRead)
def create_action_result(
    action_id: UUID,
    request: ActionResultCreate,
    session: Session = SESSION_DEPENDENCY,
) -> ActionResultRead:
    """Create action result.
    Args:
        action_id (UUID): Action execution identifier.
        request (ActionResultCreate): Action result request.
        session (Session): Active database session."""
    action = require_action(session, action_id)
    return create_result(session, action, request)


@router.get('/actions/{action_id}/results', response_model=list[ActionResultRead])
def read_action_results(action_id: UUID, session: Session = SESSION_DEPENDENCY) -> list[ActionResultRead]:
    """Read action results.
    Args:
        action_id (UUID): Action execution identifier.
        session (Session): Active database session."""
    require_action(session, action_id)
    return list_results(session, action_id)


@router.get('/learning-events', response_model=LearningEventListResponse)
def read_learning_events(
    session: Session = SESSION_DEPENDENCY,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LearningEventListResponse:
    """Read learning events.
    Args:
        session (Session): Active database session.
        limit (int): Result limit.
        offset (int): Result offset."""
    items, total = list_learning(session, project_id(), limit, offset)
    return LearningEventListResponse(items=items, total=total)


@router.get('/model-reviews', response_model=ModelReviewListResponse)
def read_model_reviews(
    session: Session = SESSION_DEPENDENCY,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ModelReviewListResponse:
    """Read model reviews.
    Args:
        session (Session): Active database session.
        limit (int): Result limit.
        offset (int): Result offset."""
    items, total = list_reviews(session, project_id(), limit, offset)
    return ModelReviewListResponse(items=items, total=total)
