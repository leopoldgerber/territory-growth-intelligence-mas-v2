from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.mas.evidence_pack import build_pack, read_latest_pack
from app.mas.llm import LLMProviderError, create_provider
from app.mas.schemas import (
    EvidenceLLMContext,
    MasAgentRunCreate,
    MasModelCallCreate,
    MasRunStatusUpdate,
    SynthesisInput,
    SynthesisOutput,
    SynthesisResponse,
)
from app.mas.service import add_agent_run, add_model_call, fail_run, update_agent_run, update_status
from app.models.tables import MasAgentRun, MasEvidencePack, MasPromptVersion, MasRun

SYNTHESIS_PROMPT_KEY = 'synthesis_agent'
SYNTHESIS_PROMPT_VERSION = 'v1'
CONFIDENCE_RANK = {'unknown': 0, 'low': 1, 'medium': 2, 'high': 3}


def ensure_prompt(session: Session) -> MasPromptVersion:
    """Ensure synthesis prompt version.
    Args:
        session (Session): Active database session."""
    record = session.scalar(
        select(MasPromptVersion).where(
            MasPromptVersion.prompt_key == SYNTHESIS_PROMPT_KEY,
            MasPromptVersion.version == SYNTHESIS_PROMPT_VERSION,
        )
    )
    if record is not None:
        return record
    record = MasPromptVersion(
        prompt_key=SYNTHESIS_PROMPT_KEY,
        version=SYNTHESIS_PROMPT_VERSION,
        description='Synthesis Agent prompt for evidence-backed analytical answers.',
        system_prompt=synthesis_prompt(),
        user_prompt_template=(
            'Use the supplied synthesis input JSON and return only a valid SynthesisOutput JSON object.'
        ),
        output_schema_json=SynthesisOutput.model_json_schema(),
        is_active=True,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def synthesis_prompt() -> str:
    """Build synthesis system prompt.
    Args:
        None (None): No arguments are required."""
    return (
        'You are a synthesis agent. Use only provided evidence. Do not calculate or invent metrics. '
        'Do not override deterministic tool outputs. If RAG or historical evidence conflicts with current analytics, '
        'current analytics wins. Use RAG only as methodology or context, never as the current metric source. '
        'Do not claim ROI, CPA, CAC, market size, or missing numeric facts unless the evidence contains them. '
        'Cite evidence_refs for important claims. Missing evidence must become limitations, not invented facts. '
        'Synthesis confidence cannot be higher than evidence_quality.overall_confidence. '
        'Return structured JSON only and match the SynthesisOutput schema.'
    )


def build_schema() -> dict[str, object]:
    """Build synthesis schema.
    Args:
        None (None): No arguments are required."""
    return SynthesisOutput.model_json_schema()


def read_pack(session: Session, request: SynthesisInput, run: MasRun) -> MasEvidencePack:
    """Read evidence pack.
    Args:
        session (Session): Active database session.
        request (SynthesisInput): Synthesis input.
        run (MasRun): MAS run record."""
    if request.force_rebuild_pack:
        return build_pack(session, run)
    if request.evidence_pack_id is not None:
        record = session.get(MasEvidencePack, request.evidence_pack_id)
        if record is None or record.mas_run_id != run.id:
            raise ValueError('Evidence pack was not found for this MAS run.')
        return record
    record = read_latest_pack(session, run.id)
    if record is not None:
        return record
    return build_pack(session, run)


def build_context(
    run: MasRun,
    pack: MasEvidencePack,
    llm_context: EvidenceLLMContext,
    request: SynthesisInput,
) -> dict[str, object]:
    """Build synthesis context.
    Args:
        run (MasRun): MAS run record.
        pack (MasEvidencePack): Evidence pack record.
        llm_context (EvidenceLLMContext): LLM-facing evidence context.
        request (SynthesisInput): Synthesis input."""
    pack_json = pack.pack_json or {}
    return {
        'mas_run_id': str(run.id),
        'evidence_pack_id': str(pack.id),
        'user_query': run.user_query,
        'intent': run.resolved_intent,
        'resolved_context': run.resolved_context_json or {},
        'evidence_context': llm_context.model_dump(mode='json'),
        'evidence_priority': pack_json.get('evidence_priority', []),
        'output_language': request.output_language,
    }


def ensure_evidence(llm_context: EvidenceLLMContext) -> EvidenceLLMContext:
    """Ensure evidence exists.
    Args:
        llm_context (EvidenceLLMContext): LLM-facing evidence context."""
    if not llm_context.key_evidence:
        raise ValueError('Evidence Pack has no usable evidence for synthesis.')
    return llm_context


def parse_output(response_json: dict[str, object]) -> SynthesisOutput:
    """Parse synthesis output.
    Args:
        response_json (dict[str, object]): LLM response JSON."""
    try:
        return SynthesisOutput.model_validate(response_json)
    except ValidationError as error:
        raise ValueError(f'Synthesis output schema validation failed: {error}') from error


def validate_output(output: SynthesisOutput, llm_context: EvidenceLLMContext) -> SynthesisOutput:
    """Validate synthesis output.
    Args:
        output (SynthesisOutput): Synthesis output.
        llm_context (EvidenceLLMContext): LLM-facing evidence context."""
    validate_refs(output, llm_context)
    apply_limit(output, llm_context)
    add_limitations(output, llm_context)
    if not output.reasoning_sections:
        raise ValueError('Synthesis output must include reasoning sections.')
    if not output.final_recommendation.strip():
        raise ValueError('Synthesis output must include final recommendation.')
    return output


def validate_refs(output: SynthesisOutput, llm_context: EvidenceLLMContext) -> SynthesisOutput:
    """Validate evidence refs.
    Args:
        output (SynthesisOutput): Synthesis output.
        llm_context (EvidenceLLMContext): LLM-facing evidence context."""
    available_refs = {item.source_ref for item in llm_context.key_evidence}
    available_ids = {source_ref.rsplit(':', 1)[-1] for source_ref in available_refs}
    collected_refs = collect_refs(output)
    if not collected_refs:
        raise ValueError('Synthesis output must cite at least one evidence_ref.')
    invalid_refs = [source_ref for source_ref in collected_refs if source_ref not in available_refs]
    if invalid_refs:
        raise ValueError(f'Synthesis output contains unknown evidence_refs: {", ".join(sorted(set(invalid_refs)))}')
    invalid_used = [
        item.evidence_id
        for item in output.evidence_used
        if item.evidence_id not in available_refs and item.evidence_id not in available_ids
    ]
    if invalid_used:
        raise ValueError(f'Synthesis output contains unknown evidence_used ids: {", ".join(sorted(set(invalid_used)))}')
    return output


def collect_refs(output: SynthesisOutput) -> list[str]:
    """Collect evidence refs.
    Args:
        output (SynthesisOutput): Synthesis output."""
    refs: list[str] = []
    for section in output.reasoning_sections:
        refs.extend(section.evidence_refs)
    for finding in output.key_findings:
        refs.extend(finding.evidence_refs)
    for risk in output.risks:
        refs.extend(risk.evidence_refs)
    for action in output.recommended_next_actions:
        refs.extend(action.evidence_refs)
    return refs


def apply_limit(output: SynthesisOutput, llm_context: EvidenceLLMContext) -> SynthesisOutput:
    """Apply confidence limit.
    Args:
        output (SynthesisOutput): Synthesis output.
        llm_context (EvidenceLLMContext): LLM-facing evidence context."""
    pack_confidence = llm_context.evidence_quality.overall_confidence
    if CONFIDENCE_RANK[output.confidence] > CONFIDENCE_RANK[pack_confidence]:
        output.confidence = pack_confidence
    return output


def add_limitations(output: SynthesisOutput, llm_context: EvidenceLLMContext) -> SynthesisOutput:
    """Add evidence limitations.
    Args:
        output (SynthesisOutput): Synthesis output.
        llm_context (EvidenceLLMContext): LLM-facing evidence context."""
    for missing_item in llm_context.missing_evidence:
        limitation = f'Missing {missing_item.type} evidence: {missing_item.reason}'
        if limitation not in output.limitations:
            output.limitations.append(limitation)
    for warning in llm_context.warnings:
        if warning not in output.limitations:
            output.limitations.append(warning)
    return output


def repair_context(
    synthesis_context: dict[str, object],
    invalid_output: dict[str, object],
    error_message: str,
) -> dict[str, object]:
    """Build repair context.
    Args:
        synthesis_context (dict[str, object]): Original synthesis context.
        invalid_output (dict[str, object]): Invalid synthesis output.
        error_message (str): Validation error message."""
    return {
        **synthesis_context,
        'invalid_output': invalid_output,
        'validation_error': error_message,
        'repair_instruction': 'Repair the output. Use only evidence_refs present in evidence_context.key_evidence.',
    }


def render_markdown(output: SynthesisOutput) -> str:
    """Render final markdown.
    Args:
        output (SynthesisOutput): Synthesis output."""
    parts = [
        '# Analytical Answer',
        '',
        '## Executive Summary',
        output.executive_summary,
        '',
        '## Final Recommendation',
        output.final_recommendation,
        '',
    ]
    parts.extend(render_sections(output))
    parts.extend(render_findings(output))
    parts.extend(render_risks(output))
    parts.extend(render_actions(output))
    parts.extend(render_limitations(output))
    parts.extend(['## Confidence', output.confidence])
    return '\n'.join(parts).strip()


def render_sections(output: SynthesisOutput) -> list[str]:
    """Render reasoning sections.
    Args:
        output (SynthesisOutput): Synthesis output."""
    parts = ['## Reasoning']
    for section in output.reasoning_sections:
        refs = ', '.join(section.evidence_refs)
        suffix = f'\nEvidence: {refs}' if refs else ''
        parts.extend([f'### {section.title}', f'{section.content}{suffix}'])
    return parts + ['']


def render_findings(output: SynthesisOutput) -> list[str]:
    """Render key findings.
    Args:
        output (SynthesisOutput): Synthesis output."""
    if not output.key_findings:
        return []
    parts = ['## Key Findings']
    for finding in output.key_findings:
        parts.append(f'- [{finding.confidence}] {finding.finding}')
    return parts + ['']


def render_risks(output: SynthesisOutput) -> list[str]:
    """Render risks.
    Args:
        output (SynthesisOutput): Synthesis output."""
    if not output.risks:
        return []
    parts = ['## Risks']
    for risk in output.risks:
        parts.append(f'- [{risk.severity}] {risk.risk} Mitigation: {risk.mitigation}')
    return parts + ['']


def render_actions(output: SynthesisOutput) -> list[str]:
    """Render next actions.
    Args:
        output (SynthesisOutput): Synthesis output."""
    if not output.recommended_next_actions:
        return []
    parts = ['## Recommended Next Actions']
    for action in output.recommended_next_actions:
        parts.append(f'- [{action.priority}] {action.action}')
    return parts + ['']


def render_limitations(output: SynthesisOutput) -> list[str]:
    """Render limitations.
    Args:
        output (SynthesisOutput): Synthesis output."""
    if not output.limitations:
        return []
    parts = ['## Limitations']
    for limitation in output.limitations:
        parts.append(f'- {limitation}')
    return parts + ['']


def save_call(
    session: Session,
    run: MasRun,
    agent_run_id: UUID,
    prompt_version_id: int,
    response: object | None,
    settings: Settings,
    status: str,
    error_message: str | None = None,
) -> None:
    """Save synthesis model call.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        agent_run_id (UUID): Synthesis agent run identifier.
        prompt_version_id (int): Prompt version identifier.
        response (object | None): LLM response.
        settings (Settings): Application settings.
        status (str): Model call status.
        error_message (str | None): Error message."""
    usage = getattr(response, 'usage', None)
    request = MasModelCallCreate(
        agent_run_id=agent_run_id,
        prompt_version_id=prompt_version_id,
        prompt_key=SYNTHESIS_PROMPT_KEY,
        provider=str(getattr(response, 'provider', settings.llm_provider)),
        model_name=str(getattr(response, 'model', settings.llm_model)),
        temperature=Decimal(str(settings.llm_temperature)),
        max_tokens=settings.llm_max_tokens,
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


def response_payload(response: object | None) -> dict[str, object] | None:
    """Build response payload.
    Args:
        response (object | None): LLM response."""
    if response is None:
        return None
    return {
        'parsed_json': getattr(response, 'parsed_json', None),
        'raw_text': getattr(response, 'raw_text', None),
        'validation_status': getattr(response, 'validation_status', None),
    }


def save_result(
    session: Session,
    run: MasRun,
    output: SynthesisOutput,
    final_answer: str,
    llm_context: EvidenceLLMContext,
) -> MasRun:
    """Save synthesis result.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        output (SynthesisOutput): Synthesis output.
        final_answer (str): Rendered final answer.
        llm_context (EvidenceLLMContext): LLM-facing evidence context."""
    status = 'completed' if llm_context.evidence_quality.completeness == 'complete' else 'partial'
    error_message = None
    if status == 'partial':
        error_message = 'Synthesis completed with incomplete evidence.'
    return update_status(
        session,
        run,
        MasRunStatusUpdate(
            status=status,
            synthesis_output_json=output.model_dump(mode='json'),
            final_answer=final_answer,
            final_summary=output.executive_summary,
            error_message=error_message,
        ),
    )


def run_synthesis(session: Session, settings: Settings, request: SynthesisInput) -> SynthesisResponse:
    """Run synthesis agent.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        request (SynthesisInput): Synthesis input."""
    run = session.get(MasRun, request.mas_run_id)
    if run is None:
        raise ValueError('MAS run was not found')
    prompt = ensure_prompt(session)
    pack = read_pack(session, request, run)
    llm_context = EvidenceLLMContext.model_validate(pack.llm_context_json)
    synthesis_context = build_context(run, pack, llm_context, request)
    agent_run = add_agent_run(
        session,
        run.id,
        MasAgentRunCreate(
            agent_name=SYNTHESIS_PROMPT_KEY,
            agent_type='llm',
            status='running',
            input_json=synthesis_context,
        ),
    )
    try:
        ensure_evidence(llm_context)
        response = call_provider(settings, prompt, synthesis_context)
        output = validate_output(parse_output(response.parsed_json or {}), llm_context)
    except LLMProviderError as error:
        update_agent_run(session, agent_run, 'failed', error_message=str(error))
        save_call(session, run, agent_run.id, prompt.id, None, settings, 'failed', str(error))
        fail_run(session, run, str(error))
        raise
    except ValueError as error:
        if str(error) == 'Evidence Pack has no usable evidence for synthesis.':
            update_agent_run(session, agent_run, 'failed', error_message=str(error))
            fail_run(session, run, str(error))
            raise
        response, output = repair_output(
            session,
            settings,
            prompt,
            run,
            agent_run,
            synthesis_context,
            llm_context,
            error,
        )
    final_answer = render_markdown(output)
    update_agent_run(session, agent_run, 'completed', output_json=output.model_dump(mode='json'))
    save_call(session, run, agent_run.id, prompt.id, response, settings, 'completed')
    save_result(session, run, output, final_answer, llm_context)
    return SynthesisResponse(
        mas_run_id=run.id,
        agent_run_id=agent_run.id,
        evidence_pack_id=pack.id,
        synthesis_output=output,
        final_answer_markdown=final_answer,
    )


def call_provider(
    settings: Settings,
    prompt: MasPromptVersion,
    synthesis_context: dict[str, object],
) -> object:
    """Call LLM provider.
    Args:
        settings (Settings): Application settings.
        prompt (MasPromptVersion): Synthesis prompt version.
        synthesis_context (dict[str, object]): Synthesis context."""
    provider = create_provider(settings)
    return provider.generate_structured(
        prompt.system_prompt or synthesis_prompt(),
        'Synthesize the supplied evidence into the requested structured analytical answer.',
        build_schema(),
        synthesis_context,
        settings.llm_temperature,
        settings.llm_max_tokens,
    )


def repair_output(
    session: Session,
    settings: Settings,
    prompt: MasPromptVersion,
    run: MasRun,
    agent_run: MasAgentRun,
    synthesis_context: dict[str, object],
    llm_context: EvidenceLLMContext,
    error: ValueError,
) -> tuple[object, SynthesisOutput]:
    """Repair synthesis output.
    Args:
        session (Session): Active database session.
        settings (Settings): Application settings.
        prompt (MasPromptVersion): Synthesis prompt version.
        run (MasRun): MAS run record.
        agent_run (MasAgentRun): Synthesis agent run record.
        synthesis_context (dict[str, object]): Synthesis context.
        llm_context (EvidenceLLMContext): LLM-facing evidence context.
        error (ValueError): Validation error."""
    invalid_output = {}
    repair_payload = repair_context(synthesis_context, invalid_output, str(error))
    try:
        response = call_provider(settings, prompt, repair_payload)
        output = validate_output(parse_output(response.parsed_json or {}), llm_context)
    except (LLMProviderError, ValueError) as repair_error:
        update_agent_run(session, agent_run, 'failed', error_message=str(repair_error))
        save_call(session, run, agent_run.id, prompt.id, None, settings, 'failed', str(repair_error))
        fail_run(session, run, str(repair_error))
        raise ValueError(str(repair_error)) from repair_error
    return response, output
