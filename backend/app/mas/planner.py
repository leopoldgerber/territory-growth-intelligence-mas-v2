from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import fetch_filter_options, resolve_project
from app.core.config import Settings
from app.mas.llm import LLMProviderError, create_provider
from app.mas.schemas import (
    AnalysisPlan,
    MasAgentRunCreate,
    MasModelCallCreate,
    MasRunCreate,
    MasRunStatusUpdate,
    PlannerAvailableFilters,
    PlannerDefaultContext,
    PlannerInput,
    PlannerResponse,
)
from app.mas.service import add_agent_run, add_model_call, create_run, fail_run, update_agent_run, update_status
from app.mas.tools import create_registry
from app.models.tables import MasPromptVersion, MasRun

PLANNER_PROMPT_KEY = 'planner_agent'
PLANNER_PROMPT_VERSION = 'v1'
PLANNER_INTENTS = {
    'market_entry_analysis',
    'existing_presence_analysis',
    'country_summary',
    'country_comparison',
    'budget_strategy_explanation',
    'saved_report_question',
    'methodology_question',
    'unknown',
}
REQUIRED_TOOLS = {
    'market_entry_analysis': [
        'country_intelligence',
        'competitor_intelligence',
        'channel_intelligence',
        'device_intelligence',
        'signals',
        'opportunity_score',
        'budget_strategy',
        'rag_retrieval',
    ],
    'existing_presence_analysis': [
        'country_intelligence',
        'competitor_intelligence',
        'channel_intelligence',
        'device_intelligence',
        'signals',
        'opportunity_score',
        'budget_strategy',
        'rag_retrieval',
    ],
    'country_summary': [
        'country_intelligence',
        'competitor_intelligence',
        'channel_intelligence',
        'device_intelligence',
        'signals',
        'opportunity_score',
        'rag_retrieval',
    ],
    'methodology_question': ['rag_retrieval'],
}


def ensure_run(session: Session, settings: Settings, request: PlannerInput) -> MasRun:
    """Ensure MAS run.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        request (PlannerInput): Planner input."""
    if request.mas_run_id is not None:
        record = session.get(MasRun, request.mas_run_id)
        if record is None:
            raise ValueError('MAS run was not found')
        return record
    default_context = request.default_context
    run_request = MasRunCreate(
        user_query=request.query,
        resolved_context_json=default_context.model_dump(mode='json'),
        strategy_mode=default_context.strategy_mode,
        date_from=default_context.date_from,
        date_to=default_context.date_to,
        budget_amount=default_context.budget_amount,
        currency=default_context.currency,
    )
    project_id = default_context.project_id or resolve_project(None, settings.default_project_id)
    return create_run(session, project_id, run_request, settings.llm_provider, settings.llm_model)


def ensure_prompt(session: Session) -> MasPromptVersion:
    """Ensure planner prompt version.
    Args:
        session (Session): Active database session."""
    record = session.scalar(
        select(MasPromptVersion).where(
            MasPromptVersion.prompt_key == PLANNER_PROMPT_KEY,
            MasPromptVersion.version == PLANNER_PROMPT_VERSION,
        )
    )
    if record is not None:
        return record
    record = MasPromptVersion(
        prompt_key=PLANNER_PROMPT_KEY,
        version=PLANNER_PROMPT_VERSION,
        description='Planner Agent prompt for structured analysis planning.',
        system_prompt=planner_system_prompt(),
        user_prompt_template='Use the supplied planner input JSON and return only a valid AnalysisPlan JSON object.',
        output_schema_json=AnalysisPlan.model_json_schema(),
        is_active=True,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def planner_system_prompt() -> str:
    """Build planner system prompt.
    Args:
        None (None): No arguments are required."""
    return (
        'You are a planning agent. Do not answer the user. Do not calculate metrics. '
        'Do not invent data. Return only structured JSON that matches the AnalysisPlan schema. '
        'Use only available tools. Use default context if provided. Ask clarification only when required values '
        'are missing. Select tools by intent and never include tools that are not listed in available_tools.'
    )


def build_filters(session: Session, settings: Settings, request: PlannerInput) -> PlannerAvailableFilters:
    """Build available planner filters.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        request (PlannerInput): Planner input."""
    if request.available_filters is not None:
        return request.available_filters
    options = fetch_filter_options(
        session=session,
        default_project_id=settings.default_project_id,
        project_id=None,
        date_from=request.default_context.date_from,
        date_to=request.default_context.date_to,
        country='all',
        tld='all',
        company='all',
        company_domain='all',
        competitors='all',
        competitor_domain='all',
    )
    return PlannerAvailableFilters(
        countries=[item.label for item in options.countries],
        companies=[item.label for item in options.companies],
    )


def build_context(
    run: MasRun,
    request: PlannerInput,
    available_filters: PlannerAvailableFilters,
    available_tools: list[str],
) -> dict[str, object]:
    """Build planner context.
    Args:
        run (MasRun): MAS run record.
        request (PlannerInput): Planner input.
        available_filters (PlannerAvailableFilters): Available filters.
        available_tools (list[str]): Available tools."""
    return {
        'mas_run_id': str(run.id),
        'user_query': request.query,
        'default_context': request.default_context.model_dump(mode='json'),
        'available_filters': available_filters.model_dump(mode='json'),
        'available_tools': available_tools,
    }


def build_schema() -> dict[str, object]:
    """Build structured output schema.
    Args:
        None (None): No arguments are required."""
    return AnalysisPlan.model_json_schema()


def parse_plan(response_json: dict[str, object]) -> AnalysisPlan:
    """Parse analysis plan.
    Args:
        response_json (dict[str, object]): Planner response JSON."""
    try:
        return AnalysisPlan.model_validate(response_json)
    except ValidationError as error:
        raise ValueError(f'Planner output schema validation failed: {error}') from error


def validate_plan(
    plan: AnalysisPlan,
    request: PlannerInput,
    available_filters: PlannerAvailableFilters,
    available_tools: list[str],
) -> AnalysisPlan:
    """Validate analysis plan.
    Args:
        plan (AnalysisPlan): Analysis plan.
        request (PlannerInput): Planner input.
        available_filters (PlannerAvailableFilters): Available filters.
        available_tools (list[str]): Available tools."""
    if plan.intent not in PLANNER_INTENTS:
        plan.intent = 'unknown'
        plan.clarification_needed = True
        plan.clarification_questions.append('Please clarify what analysis you need.')
    requested_tools = plan.required_tools + plan.optional_tools
    unknown_tools = [tool_name for tool_name in requested_tools if tool_name not in available_tools]
    if unknown_tools:
        raise ValueError(f'Planner returned unknown tools: {", ".join(unknown_tools)}')
    plan.required_tools = normalize_tools(plan.intent, plan.required_tools, available_tools)
    plan = apply_defaults(plan, request.default_context)
    plan = validate_values(plan, available_filters)
    plan = validate_missing(plan)
    return plan


def normalize_tools(intent: str, requested_tools: list[str], available_tools: list[str]) -> list[str]:
    """Normalize required tools.
    Args:
        intent (str): Planner intent.
        requested_tools (list[str]): Requested tools.
        available_tools (list[str]): Available tools."""
    fallback_tools = ['rag_retrieval'] if intent in {'methodology_question', 'unknown'} else []
    default_tools = REQUIRED_TOOLS.get(intent, fallback_tools)
    tools = requested_tools or default_tools
    return [tool_name for tool_name in tools if tool_name in available_tools]


def apply_defaults(plan: AnalysisPlan, default_context: PlannerDefaultContext) -> AnalysisPlan:
    """Apply default context.
    Args:
        plan (AnalysisPlan): Analysis plan.
        default_context (PlannerDefaultContext): Default context."""
    context = plan.resolved_context
    context.project_id = context.project_id or default_context.project_id
    context.country = context.country or default_context.country
    context.company = context.company or default_context.company
    context.date_from = context.date_from or default_context.date_from
    context.date_to = context.date_to or default_context.date_to
    context.budget_amount = context.budget_amount or default_context.budget_amount
    context.currency = context.currency or default_context.currency
    context.context_hash = context.context_hash or default_context.context_hash
    if plan.strategy_mode is None:
        plan.strategy_mode = default_context.strategy_mode
    return plan


def validate_values(plan: AnalysisPlan, available_filters: PlannerAvailableFilters) -> AnalysisPlan:
    """Validate planner values.
    Args:
        plan (AnalysisPlan): Analysis plan.
        available_filters (PlannerAvailableFilters): Available filters."""
    context = plan.resolved_context
    if plan.strategy_mode not in {'market_entry', 'existing_presence', None}:
        plan.clarification_needed = True
        add_missing(plan, 'strategy_mode')
    if context.currency is not None and context.currency not in available_filters.currencies:
        plan.clarification_needed = True
        add_missing(plan, 'currency')
    if context.country is not None and available_filters.countries:
        if context.country.lower() not in {country.lower() for country in available_filters.countries}:
            plan.clarification_needed = True
            add_missing(plan, 'country')
    if context.company is not None and available_filters.companies:
        if context.company.lower() not in {company.lower() for company in available_filters.companies}:
            plan.clarification_needed = True
            add_missing(plan, 'company')
    return plan


def validate_missing(plan: AnalysisPlan) -> AnalysisPlan:
    """Validate missing inputs.
    Args:
        plan (AnalysisPlan): Analysis plan."""
    context = plan.resolved_context
    required_inputs = required_inputs_for(plan.intent)
    values = {
        'country': context.country,
        'company': context.company,
        'date_from': context.date_from,
        'date_to': context.date_to,
        'budget_amount': context.budget_amount,
        'currency': context.currency,
        'strategy_mode': plan.strategy_mode,
    }
    for input_name in required_inputs:
        if values.get(input_name) in {None, ''}:
            add_missing(plan, input_name)
    if plan.missing_required_inputs:
        plan.clarification_needed = True
        add_questions(plan)
    return plan


def required_inputs_for(intent: str) -> list[str]:
    """Read required inputs.
    Args:
        intent (str): Planner intent."""
    if intent in {'market_entry_analysis', 'existing_presence_analysis'}:
        return ['country', 'company', 'date_from', 'date_to', 'budget_amount', 'currency', 'strategy_mode']
    if intent in {'country_summary', 'country_comparison'}:
        return ['country', 'date_from', 'date_to']
    if intent == 'budget_strategy_explanation':
        return ['country', 'date_from', 'date_to']
    if intent == 'methodology_question':
        return []
    return []


def add_missing(plan: AnalysisPlan, input_name: str) -> AnalysisPlan:
    """Add missing input.
    Args:
        plan (AnalysisPlan): Analysis plan.
        input_name (str): Missing input name."""
    if input_name not in plan.missing_required_inputs:
        plan.missing_required_inputs.append(input_name)
    return plan


def add_questions(plan: AnalysisPlan) -> AnalysisPlan:
    """Add clarification questions.
    Args:
        plan (AnalysisPlan): Analysis plan."""
    question_map = {
        'country': 'Which country should be analyzed?',
        'company': 'Which company should be analyzed?',
        'date_from': 'What start date should be used?',
        'date_to': 'What end date should be used?',
        'budget_amount': 'What budget amount should be used?',
        'currency': 'Which currency should be used?',
        'strategy_mode': 'Should this be market entry or existing presence analysis?',
    }
    for input_name in plan.missing_required_inputs:
        question = question_map.get(input_name)
        if question is not None and question not in plan.clarification_questions:
            plan.clarification_questions.append(question)
    return plan


def save_success(
    session: Session,
    run: MasRun,
    agent_run_id: UUID,
    prompt_version_id: int,
    plan: AnalysisPlan,
) -> MasRun:
    """Save successful planner result.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        agent_run_id (UUID): Planner agent run identifier.
        prompt_version_id (int): Prompt version identifier.
        plan (AnalysisPlan): Analysis plan."""
    run.prompt_version_id = prompt_version_id
    status = 'needs_clarification' if plan.clarification_needed else 'running'
    request = MasRunStatusUpdate(
        status=status,
        planner_output_json=plan.model_dump(mode='json'),
    )
    run.resolved_intent = plan.intent
    run.resolved_context_json = plan.resolved_context.model_dump(mode='json')
    updated_run = update_status(session, run, request)
    session.refresh(updated_run)
    return updated_run


def save_model_call(
    session: Session,
    run: MasRun,
    agent_run_id: UUID,
    prompt_version_id: int,
    response: object,
    status: str,
    error_message: str | None = None,
) -> None:
    """Save planner model call.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        agent_run_id (UUID): Planner agent run identifier.
        prompt_version_id (int): Prompt version identifier.
        response (object): LLM response.
        status (str): Model call status.
        error_message (str | None): Error message."""
    usage = getattr(response, 'usage', None)
    request = MasModelCallCreate(
        agent_run_id=agent_run_id,
        prompt_version_id=prompt_version_id,
        prompt_key=PLANNER_PROMPT_KEY,
        provider=str(getattr(response, 'provider', 'unknown')),
        model_name=str(getattr(response, 'model', 'unknown')),
        temperature=None,
        max_tokens=None,
        structured_output_enabled=True,
        input_tokens=getattr(usage, 'input_tokens', None),
        output_tokens=getattr(usage, 'output_tokens', None),
        total_tokens=getattr(usage, 'total_tokens', None),
        estimated_cost=getattr(usage, 'estimated_cost', None),
        latency_ms=getattr(response, 'latency_ms', None),
        status=status,
        error_message=error_message,
        raw_response_json=response_payload(response),
    )
    add_model_call(session, run.id, request)


def response_payload(response: object) -> dict[str, object] | None:
    """Build response payload.
    Args:
        response (object): LLM response."""
    if response is None:
        return None
    parsed_json = getattr(response, 'parsed_json', None)
    raw_text = getattr(response, 'raw_text', None)
    validation_status = getattr(response, 'validation_status', None)
    return {
        'parsed_json': parsed_json,
        'raw_text': raw_text,
        'validation_status': validation_status,
    }


def plan_analysis(session: Session, settings: Settings, request: PlannerInput) -> PlannerResponse:
    """Plan MAS analysis.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        request (PlannerInput): Planner input."""
    run = ensure_run(session, settings, request)
    prompt = ensure_prompt(session)
    registry = create_registry()
    available_tools = [item.tool_name for item in registry.list_tools()]
    available_filters = build_filters(session, settings, request)
    planner_context = build_context(run, request, available_filters, available_tools)
    agent_run = add_agent_run(
        session,
        run.id,
        MasAgentRunCreate(
            agent_name=PLANNER_PROMPT_KEY,
            agent_type='llm',
            status='running',
            input_json=planner_context,
        ),
    )
    try:
        provider = create_provider(settings)
        response = provider.generate_structured(
            prompt.system_prompt or planner_system_prompt(),
            request.query,
            build_schema(),
            planner_context,
            settings.llm_temperature,
            settings.llm_max_tokens,
        )
        parsed_json = response.parsed_json or {}
        plan = validate_plan(parse_plan(parsed_json), request, available_filters, available_tools)
    except LLMProviderError as error:
        update_agent_run(session, agent_run, 'failed', error_message=str(error))
        save_model_call(session, run, agent_run.id, prompt.id, None, 'failed', str(error))
        fail_run(session, run, str(error))
        raise
    except ValueError as error:
        update_agent_run(session, agent_run, 'failed', error_message=str(error))
        save_model_call(session, run, agent_run.id, prompt.id, None, 'failed', str(error))
        fail_run(session, run, str(error))
        raise
    update_agent_run(session, agent_run, 'completed', output_json=plan.model_dump(mode='json'))
    save_model_call(session, run, agent_run.id, prompt.id, response, 'completed')
    save_success(session, run, agent_run.id, prompt.id, plan)
    return PlannerResponse(mas_run_id=run.id, agent_run_id=agent_run.id, plan=plan)
