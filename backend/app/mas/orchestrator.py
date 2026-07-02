import hashlib
import json
import time
from datetime import date
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import resolve_project
from app.core.config import Settings
from app.history.service import build_history
from app.mas.evidence_pack import build_pack
from app.mas.planner import plan_analysis
from app.mas.schemas import (
    AnalysisPlan,
    MasEvidenceItemCreate,
    MasRunCreate,
    MasRunOptions,
    MasRunStatusUpdate,
    MasToolCallCreate,
    MasWorkflowRequest,
    MasWorkflowResponse,
    PlannerDefaultContext,
    PlannerInput,
    SynthesisInput,
    ToolContext,
    ToolResult,
)
from app.mas.service import (
    add_evidence_item,
    add_tool_call,
    count_runs,
    create_run,
    fail_run,
    list_evidence,
    list_model_calls,
    list_runs,
    list_tool_calls,
    update_status,
)
from app.mas.synthesis import run_synthesis
from app.mas.tools import create_registry
from app.models.tables import DimCompany, DimCountry, MasRun

CRITICAL_TOOLS = {
    'market_entry': {
        'country_intelligence',
        'competitor_intelligence',
        'channel_intelligence',
        'opportunity_score',
        'budget_strategy',
    },
    'existing_presence': {
        'country_intelligence',
        'competitor_intelligence',
        'channel_intelligence',
        'opportunity_score',
        'budget_strategy',
    },
    'default': {'country_intelligence', 'channel_intelligence'},
}


def run_workflow(session: Session, settings: Settings, request: MasWorkflowRequest) -> MasWorkflowResponse:
    """Run MAS workflow.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        request (MasWorkflowRequest): MAS workflow request."""
    started_at = time.perf_counter()
    run = create_workflow(session, settings, request)
    if request.options.run_mode == 'async':
        return build_response(session, run, [])
    warnings: list[str] = []
    try:
        plan = execute_planner(session, settings, run, request)
        session.refresh(run)
        if plan.clarification_needed:
            return build_response(session, run, warnings)
        tool_context = build_context(session, run, plan.resolved_context, plan.strategy_mode)
        warnings.extend(execute_tools(session, settings, run, plan, tool_context, request.options))
        pack = build_evidence(session, run)
        synthesis = run_synthesis(
            session,
            settings,
            SynthesisInput(mas_run_id=run.id, evidence_pack_id=pack.id, output_language='ru'),
        )
        session.refresh(run)
        warnings.extend(synthesis.synthesis_output.limitations)
        save_history(session, run, warnings)
        save_metrics(session, run, started_at, warnings)
        return build_response(session, run, warnings)
    except Exception as error:
        fail_run(session, run, str(error))
        save_metrics(session, run, started_at, warnings)
        raise


def create_workflow(session: Session, settings: Settings, request: MasWorkflowRequest) -> MasRun:
    """Create workflow run.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        request (MasWorkflowRequest): MAS workflow request."""
    default_context = request.default_context
    project_id = request.project_id or default_context.project_id or resolve_project(None, settings.default_project_id)
    run_request = MasRunCreate(
        user_query=request.user_query,
        created_by=request.created_by,
        resolved_context_json=default_context.model_dump(mode='json'),
        strategy_mode=default_context.strategy_mode,
        date_from=default_context.date_from,
        date_to=default_context.date_to,
        budget_amount=default_context.budget_amount,
        currency=default_context.currency,
    )
    return create_run(session, project_id, run_request, settings.llm_provider, settings.llm_model)


def execute_planner(
    session: Session,
    settings: Settings,
    run: MasRun,
    request: MasWorkflowRequest,
) -> AnalysisPlan:
    """Execute planner.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        run (MasRun): MAS run record.
        request (MasWorkflowRequest): MAS workflow request."""
    planner_request = PlannerInput(
        mas_run_id=run.id,
        query=request.user_query,
        default_context=merge_context(run.project_id, request.default_context),
    )
    response = plan_analysis(session, settings, planner_request)
    sync_context(session, run, response.plan)
    return response.plan


def merge_context(project_id: UUID, default_context: PlannerDefaultContext) -> PlannerDefaultContext:
    """Merge planner context.
    Args:
        project_id (UUID): Project identifier.
        default_context (PlannerDefaultContext): Default planner context."""
    data = default_context.model_dump()
    data['project_id'] = default_context.project_id or project_id
    return PlannerDefaultContext(**data)


def sync_context(session: Session, run: MasRun, plan: AnalysisPlan) -> MasRun:
    """Sync planned context.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        plan (AnalysisPlan): Analysis plan."""
    context = plan.resolved_context
    country = find_country(session, context.country)
    company = find_company(session, context.company)
    run.strategy_mode = plan.strategy_mode
    run.country_id = country.id if country is not None else run.country_id
    run.company_id = company.id if company is not None else run.company_id
    run.date_from = context.date_from or run.date_from
    run.date_to = context.date_to or run.date_to
    run.budget_amount = context.budget_amount or run.budget_amount
    run.currency = context.currency or run.currency
    session.commit()
    session.refresh(run)
    return run


def build_context(
    session: Session,
    run: MasRun,
    resolved_context: object,
    strategy_mode: str | None,
) -> ToolContext:
    """Build tool context.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        resolved_context (object): Planner resolved context.
        strategy_mode (str | None): Strategy mode."""
    country = find_country(session, getattr(resolved_context, 'country', None))
    company = find_company(session, getattr(resolved_context, 'company', None))
    context_hash = build_hash(run, resolved_context, strategy_mode)
    return ToolContext(
        project_id=run.project_id,
        strategy_mode=strategy_mode,
        country_id=country.id if country is not None else run.country_id,
        country_code=country.iso2 if country is not None else None,
        country_name=country.country_name_en if country is not None else getattr(resolved_context, 'country', None),
        company_id=company.id if company is not None else run.company_id,
        company_name=company.name if company is not None else getattr(resolved_context, 'company', None),
        date_from=getattr(resolved_context, 'date_from', None) or run.date_from,
        date_to=getattr(resolved_context, 'date_to', None) or run.date_to,
        budget_amount=getattr(resolved_context, 'budget_amount', None) or run.budget_amount,
        currency=getattr(resolved_context, 'currency', None) or run.currency,
        context_hash=context_hash,
    )


def execute_tools(
    session: Session,
    settings: Settings,
    run: MasRun,
    plan: AnalysisPlan,
    context: ToolContext,
    options: MasRunOptions,
) -> list[str]:
    """Execute planned tools.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        run (MasRun): MAS run record.
        plan (AnalysisPlan): Analysis plan.
        context (ToolContext): Tool context.
        options (MasRunOptions): MAS run options."""
    warnings: list[str] = []
    registry = create_registry()
    tool_names = planned_tools(plan, options)
    for tool_name in tool_names:
        tool = registry.get_tool(tool_name)
        if tool is None:
            warnings.append(f'Tool {tool_name} is not registered.')
            continue
        result = tool.run(session, settings, context, tool_params(tool_name, run))
        persist_tool(session, run, result)
        if result.status == 'failed':
            message = '; '.join(result.errors) or f'{tool_name} failed.'
            if is_critical(plan.strategy_mode, tool_name):
                raise ValueError(f'Critical tool failed: {tool_name}: {message}')
            warnings.append(f'{tool_name} failed; workflow continued with partial evidence.')
            continue
        if result.warnings:
            warnings.extend(result.warnings)
        persist_evidence(session, run, result)
    return warnings


def planned_tools(plan: AnalysisPlan, options: MasRunOptions) -> list[str]:
    """Build planned tools.
    Args:
        plan (AnalysisPlan): Analysis plan.
        options (MasRunOptions): MAS run options."""
    tool_names = list(dict.fromkeys(plan.required_tools + plan.optional_tools))
    if not options.use_rag:
        return [tool_name for tool_name in tool_names if tool_name != 'rag_retrieval']
    return tool_names


def tool_params(tool_name: str, run: MasRun) -> dict[str, object]:
    """Build tool parameters.
    Args:
        tool_name (str): Tool name.
        run (MasRun): MAS run record."""
    if tool_name == 'rag_retrieval':
        return {'query': run.user_query, 'top_k': 5}
    return {'limit': 20}


def persist_tool(session: Session, run: MasRun, result: ToolResult) -> ToolResult:
    """Persist tool call.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        result (ToolResult): Tool result."""
    request = MasToolCallCreate(
        tool_name=result.tool_name,
        tool_type='retrieval' if result.tool_name == 'rag_retrieval' else 'analytics',
        status=tool_status(result.status),
        input_json={'context': result.context.model_dump(mode='json')},
        output_json=result.model_dump(mode='json'),
        error_message='; '.join(result.errors) if result.errors else None,
    )
    add_tool_call(session, run.id, request)
    return result


def persist_evidence(session: Session, run: MasRun, result: ToolResult) -> ToolResult:
    """Persist evidence item.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        result (ToolResult): Tool result."""
    request = MasEvidenceItemCreate(
        source_type=evidence_source(result.source),
        evidence_type=evidence_type(result.evidence_type),
        source_table=evidence_table(result),
        source_record_id=evidence_record(result),
        context_hash=result.context.context_hash,
        title=f'{result.tool_name} evidence',
        summary=result.summary,
        data_json=result.model_dump(mode='json'),
        confidence=evidence_confidence(result.confidence),
    )
    add_evidence_item(session, run.id, request)
    return result


def build_evidence(session: Session, run: MasRun) -> object:
    """Build evidence pack.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record."""
    pack = build_pack(session, run)
    if not pack.llm_context_json.get('key_evidence'):
        raise ValueError('Evidence Pack has no usable evidence for workflow synthesis.')
    return pack


def save_metrics(session: Session, run: MasRun, started_at: float, warnings: list[str]) -> MasRun:
    """Save workflow metrics.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        started_at (float): Workflow start marker.
        warnings (list[str]): Workflow warnings."""
    metrics = {
        'duration_ms': int((time.perf_counter() - started_at) * 1000),
        'tool_count': len(list_tool_calls(session, run.id)),
        'evidence_count': len(list_evidence(session, run.id)),
        'model_call_count': len(list_model_calls(session, run.id)),
        'rag_results_count': run.rag_results_count,
        'warnings': warnings,
    }
    return update_status(session, run, MasRunStatusUpdate(status=run.status, metrics_json=metrics))


def save_history(session: Session, run: MasRun, warnings: list[str]) -> MasRun:
    """Save workflow history.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        warnings (list[str]): Workflow warnings."""
    try:
        build_history(session, run)
    except Exception as error:
        warnings.append(f'History extraction failed: {error}')
    session.refresh(run)
    return run


def build_response(session: Session, run: MasRun, warnings: list[str]) -> MasWorkflowResponse:
    """Build workflow response.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        warnings (list[str]): Workflow warnings."""
    session.refresh(run)
    planner_output = run.planner_output_json or {}
    clarification_questions = planner_output.get('clarification_questions', [])
    if not isinstance(clarification_questions, list):
        clarification_questions = []
    synthesis_output = run.synthesis_output_json or {}
    return MasWorkflowResponse(
        mas_run_id=run.id,
        status=run.status,
        resolved_intent=run.resolved_intent,
        resolved_context=run.resolved_context_json or {},
        final_answer=run.final_answer,
        final_summary=run.final_summary,
        confidence=str(synthesis_output.get('confidence')) if synthesis_output.get('confidence') else None,
        evidence_count=len(list_evidence(session, run.id)),
        warnings=warnings,
        clarification_questions=[str(item) for item in clarification_questions],
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


def list_workflows(
    session: Session,
    project_id: UUID,
    status: str | None,
    intent: str | None,
    strategy_mode: str | None,
    country: str | None,
    company: str | None,
    date_from: date | None,
    date_to: date | None,
    limit: int,
    offset: int,
) -> tuple[list[MasRun], int]:
    """List workflow runs.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        status (str | None): Optional status filter.
        intent (str | None): Optional intent filter.
        strategy_mode (str | None): Optional strategy mode filter.
        country (str | None): Optional country filter.
        company (str | None): Optional company filter.
        date_from (date | None): Optional created from date.
        date_to (date | None): Optional created to date.
        limit (int): Result limit.
        offset (int): Result offset."""
    items = list_runs(
        session,
        project_id,
        status,
        limit,
        intent,
        strategy_mode,
        country,
        company,
        date_from,
        date_to,
        offset,
    )
    total = count_runs(session, project_id, status, intent, strategy_mode, country, company, date_from, date_to)
    return items, total


def find_country(session: Session, value: str | None) -> DimCountry | None:
    """Find country.
    Args:
        session (Session): Active database session.
        value (str | None): Country value."""
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized or normalized in {'all', 'none'}:
        return None
    return session.scalar(
        select(DimCountry).where(
            or_(
                DimCountry.country_name_en.ilike(value),
                DimCountry.iso2.ilike(value),
                DimCountry.iso3.ilike(value),
            )
        )
    )


def find_company(session: Session, value: str | None) -> DimCompany | None:
    """Find company.
    Args:
        session (Session): Active database session.
        value (str | None): Company value."""
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized or normalized in {'all', 'none'}:
        return None
    return session.scalar(
        select(DimCompany).where(
            or_(
                DimCompany.name.ilike(value),
                DimCompany.normalized_name == normalized,
            )
        )
    )


def build_hash(run: MasRun, resolved_context: object, strategy_mode: str | None) -> str:
    """Build context hash.
    Args:
        run (MasRun): MAS run record.
        resolved_context (object): Planner resolved context.
        strategy_mode (str | None): Strategy mode."""
    payload = {
        'run_id': str(run.id),
        'project_id': str(run.project_id),
        'strategy_mode': strategy_mode,
        'context': getattr(resolved_context, 'model_dump', lambda **_: {})(mode='json'),
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def is_critical(strategy_mode: str | None, tool_name: str) -> bool:
    """Check critical tool.
    Args:
        strategy_mode (str | None): Strategy mode.
        tool_name (str): Tool name."""
    critical_tools = CRITICAL_TOOLS.get(strategy_mode or 'default', CRITICAL_TOOLS['default'])
    return tool_name in critical_tools


def tool_status(status: str) -> str:
    """Map tool status.
    Args:
        status (str): Tool status."""
    if status == 'failed':
        return 'failed'
    if status == 'skipped':
        return 'skipped'
    if status == 'partial':
        return 'partial'
    return 'completed'


def evidence_source(source: str) -> str:
    """Map evidence source.
    Args:
        source (str): Tool source."""
    if source == 'budget_strategy_report':
        return 'budget_strategy'
    if source in {'analytics_db', 'derived_signal', 'opportunity_score', 'rag', 'report', 'user_input', 'llm_output'}:
        return source
    return 'analytics_db'


def evidence_type(evidence_type_value: str) -> str:
    """Map evidence type.
    Args:
        evidence_type_value (str): Tool evidence type."""
    allowed_types = {
        'country',
        'competitor',
        'channel',
        'device',
        'signal',
        'opportunity_score',
        'budget_strategy',
        'methodology',
        'historical_report',
        'company_profile',
    }
    if evidence_type_value in allowed_types:
        return evidence_type_value
    return 'methodology'


def evidence_confidence(confidence: str) -> str:
    """Map evidence confidence.
    Args:
        confidence (str): Tool confidence."""
    if confidence in {'high', 'medium', 'low'}:
        return confidence
    return 'medium'


def evidence_table(result: ToolResult) -> str | None:
    """Read evidence source table.
    Args:
        result (ToolResult): Tool result."""
    if not result.source_refs:
        return None
    return result.source_refs[0].source_name


def evidence_record(result: ToolResult) -> str | None:
    """Read evidence source record.
    Args:
        result (ToolResult): Tool result."""
    if not result.source_refs:
        return None
    return result.source_refs[0].record_id
