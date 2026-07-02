from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.mas.schemas import (
    MasAgentRunCreate,
    MasEvidenceItemCreate,
    MasModelCallCreate,
    MasRunCreate,
    MasRunStatusUpdate,
    MasToolCallCreate,
)
from app.models.tables import MasAgentRun, MasEvidenceItem, MasModelCall, MasRun, MasToolCall

TERMINAL_STATUSES = {'completed', 'partial', 'failed', 'cancelled'}
STARTED_STATUSES = {'running', 'needs_clarification', 'completed', 'partial', 'failed', 'cancelled'}


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def create_run(
    session: Session,
    project_id: UUID,
    request: MasRunCreate,
    default_llm_provider: str | None = None,
    default_llm_model: str | None = None,
) -> MasRun:
    """Create MAS run.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (MasRunCreate): MAS run create payload.
        default_llm_provider (str | None): Default LLM provider.
        default_llm_model (str | None): Default LLM model."""
    record = MasRun(
        project_id=project_id,
        created_by=request.created_by,
        status='pending',
        user_query=request.user_query,
        resolved_intent=request.resolved_intent,
        resolved_context_json=request.resolved_context_json,
        strategy_mode=request.strategy_mode,
        country_id=request.country_id,
        company_id=request.company_id,
        date_from=request.date_from,
        date_to=request.date_to,
        budget_amount=request.budget_amount,
        currency=request.currency,
        default_llm_provider=default_llm_provider,
        default_llm_model=default_llm_model,
        prompt_version_id=request.prompt_version_id,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def read_run(session: Session, project_id: UUID, run_id: UUID) -> MasRun | None:
    """Read MAS run.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        run_id (UUID): MAS run identifier."""
    return session.scalar(select(MasRun).where(MasRun.project_id == project_id, MasRun.id == run_id))


def list_runs(
    session: Session,
    project_id: UUID,
    status: str | None,
    limit: int,
    intent: str | None = None,
    strategy_mode: str | None = None,
    country: str | None = None,
    company: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: int = 0,
) -> list[MasRun]:
    """List MAS runs.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        status (str | None): Optional status filter.
        limit (int): Result limit.
        intent (str | None): Optional intent filter.
        strategy_mode (str | None): Optional strategy mode filter.
        country (str | None): Optional country filter.
        company (str | None): Optional company filter.
        date_from (date | None): Optional created from date.
        date_to (date | None): Optional created to date.
        offset (int): Result offset."""
    filters = build_filters(project_id, status, intent, strategy_mode, country, company, date_from, date_to)
    return list(
        session.scalars(
            select(MasRun)
            .where(*filters)
            .order_by(MasRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )


def count_runs(
    session: Session,
    project_id: UUID,
    status: str | None,
    intent: str | None = None,
    strategy_mode: str | None = None,
    country: str | None = None,
    company: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> int:
    """Count MAS runs.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        status (str | None): Optional status filter.
        intent (str | None): Optional intent filter.
        strategy_mode (str | None): Optional strategy mode filter.
        country (str | None): Optional country filter.
        company (str | None): Optional company filter.
        date_from (date | None): Optional created from date.
        date_to (date | None): Optional created to date."""
    filters = build_filters(project_id, status, intent, strategy_mode, country, company, date_from, date_to)
    return int(session.scalar(select(func.count()).select_from(MasRun).where(*filters)) or 0)


def build_filters(
    project_id: UUID,
    status: str | None,
    intent: str | None,
    strategy_mode: str | None,
    country: str | None,
    company: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[object]:
    """Build MAS run filters.
    Args:
        project_id (UUID): Project identifier.
        status (str | None): Optional status filter.
        intent (str | None): Optional intent filter.
        strategy_mode (str | None): Optional strategy mode filter.
        country (str | None): Optional country filter.
        company (str | None): Optional company filter.
        date_from (date | None): Optional created from date.
        date_to (date | None): Optional created to date."""
    filters: list[object] = [MasRun.project_id == project_id]
    if status is not None:
        filters.append(MasRun.status == status)
    if intent is not None:
        filters.append(MasRun.resolved_intent == intent)
    if strategy_mode is not None:
        filters.append(MasRun.strategy_mode == strategy_mode)
    if country is not None:
        filters.append(MasRun.resolved_context_json['country'].astext == country)
    if company is not None:
        filters.append(MasRun.resolved_context_json['company'].astext == company)
    if date_from is not None:
        filters.append(MasRun.created_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC))
    if date_to is not None:
        filters.append(MasRun.created_at <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC))
    return filters


def update_status(session: Session, record: MasRun, request: MasRunStatusUpdate) -> MasRun:
    """Update MAS run status.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record.
        request (MasRunStatusUpdate): Status update payload."""
    timestamp = current_time()
    record.status = request.status
    record.updated_at = timestamp
    if request.status in STARTED_STATUSES and record.started_at is None:
        record.started_at = timestamp
    if request.status in TERMINAL_STATUSES:
        record.completed_at = timestamp
    if request.planner_output_json is not None:
        record.planner_output_json = request.planner_output_json
    if request.synthesis_output_json is not None:
        record.synthesis_output_json = request.synthesis_output_json
    if request.metrics_json is not None:
        record.metrics_json = request.metrics_json
    if request.final_answer is not None:
        record.final_answer = request.final_answer
    if request.final_summary is not None:
        record.final_summary = request.final_summary
    if request.error_message is not None:
        record.error_message = request.error_message
    session.commit()
    session.refresh(record)
    return record


def start_run(session: Session, record: MasRun) -> MasRun:
    """Start MAS run.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record."""
    return update_status(session, record, MasRunStatusUpdate(status='running'))


def complete_run(session: Session, record: MasRun, final_answer: str, final_summary: str | None = None) -> MasRun:
    """Complete MAS run.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record.
        final_answer (str): Final answer text.
        final_summary (str | None): Optional final summary."""
    request = MasRunStatusUpdate(status='completed', final_answer=final_answer, final_summary=final_summary)
    return update_status(session, record, request)


def mark_partial(session: Session, record: MasRun, final_answer: str, error_message: str | None = None) -> MasRun:
    """Mark MAS run partial.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record.
        final_answer (str): Final answer text.
        error_message (str | None): Optional partial reason."""
    request = MasRunStatusUpdate(status='partial', final_answer=final_answer, error_message=error_message)
    return update_status(session, record, request)


def fail_run(session: Session, record: MasRun, error_message: str) -> MasRun:
    """Fail MAS run.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record.
        error_message (str): Failure reason."""
    return update_status(session, record, MasRunStatusUpdate(status='failed', error_message=error_message))


def add_agent_run(session: Session, run_id: UUID, request: MasAgentRunCreate) -> MasAgentRun:
    """Add MAS agent run.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (MasAgentRunCreate): Agent run create payload."""
    timestamp = current_time()
    record = MasAgentRun(
        mas_run_id=run_id,
        agent_name=request.agent_name,
        agent_type=request.agent_type,
        status=request.status,
        input_json=request.input_json,
        output_json=request.output_json,
        error_message=request.error_message,
        started_at=timestamp if request.status in STARTED_STATUSES else None,
        completed_at=timestamp if request.status in TERMINAL_STATUSES else None,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def update_agent_run(
    session: Session,
    record: MasAgentRun,
    status: str,
    output_json: dict[str, object] | None = None,
    error_message: str | None = None,
) -> MasAgentRun:
    """Update MAS agent run.
    Args:
        session (Session): Active database session.
        record (MasAgentRun): MAS agent run record.
        status (str): Agent run status.
        output_json (dict[str, object] | None): Agent output payload.
        error_message (str | None): Error message."""
    timestamp = current_time()
    record.status = status
    if record.started_at is None:
        record.started_at = timestamp
    if status in TERMINAL_STATUSES:
        record.completed_at = timestamp
    if output_json is not None:
        record.output_json = output_json
    if error_message is not None:
        record.error_message = error_message
    session.commit()
    session.refresh(record)
    return record


def add_tool_call(session: Session, run_id: UUID, request: MasToolCallCreate) -> MasToolCall:
    """Add MAS tool call.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (MasToolCallCreate): Tool call create payload."""
    record = MasToolCall(
        mas_run_id=run_id,
        agent_run_id=request.agent_run_id,
        tool_name=request.tool_name,
        tool_type=request.tool_type,
        status=request.status,
        input_json=request.input_json,
        output_json=request.output_json,
        error_message=request.error_message,
        duration_ms=request.duration_ms,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def add_evidence_item(session: Session, run_id: UUID, request: MasEvidenceItemCreate) -> MasEvidenceItem:
    """Add MAS evidence item.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (MasEvidenceItemCreate): Evidence item create payload."""
    record = MasEvidenceItem(
        mas_run_id=run_id,
        source_type=request.source_type,
        evidence_type=request.evidence_type,
        source_table=request.source_table,
        source_record_id=request.source_record_id,
        context_hash=request.context_hash,
        title=request.title,
        summary=request.summary,
        data_json=request.data_json,
        confidence=request.confidence,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_evidence(session: Session, run_id: UUID) -> list[MasEvidenceItem]:
    """List MAS evidence items.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    return list(
        session.scalars(
            select(MasEvidenceItem)
            .where(MasEvidenceItem.mas_run_id == run_id)
            .order_by(MasEvidenceItem.created_at)
        ).all()
    )


def list_tool_calls(session: Session, run_id: UUID) -> list[MasToolCall]:
    """List MAS tool calls.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    return list(
        session.scalars(
            select(MasToolCall)
            .where(MasToolCall.mas_run_id == run_id)
            .order_by(MasToolCall.created_at)
        ).all()
    )


def add_model_call(session: Session, run_id: UUID, request: MasModelCallCreate) -> MasModelCall:
    """Add MAS model call.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (MasModelCallCreate): Model call create payload."""
    record = MasModelCall(
        mas_run_id=run_id,
        agent_run_id=request.agent_run_id,
        prompt_version_id=request.prompt_version_id,
        prompt_key=request.prompt_key,
        provider=request.provider,
        model_name=request.model_name,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        structured_output_enabled=request.structured_output_enabled,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        total_tokens=request.total_tokens,
        estimated_cost=request.estimated_cost,
        latency_ms=request.latency_ms,
        status=request.status,
        error_message=request.error_message,
        raw_response_json=request.raw_response_json,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_model_calls(session: Session, run_id: UUID) -> list[MasModelCall]:
    """List MAS model calls.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    return list(
        session.scalars(
            select(MasModelCall)
            .where(MasModelCall.mas_run_id == run_id)
            .order_by(MasModelCall.created_at)
        ).all()
    )
