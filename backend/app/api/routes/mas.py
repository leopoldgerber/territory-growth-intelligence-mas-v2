from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.country_intelligence import resolve_project
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.history.service import build_history
from app.mas.evidence_pack import build_pack, read_latest_pack
from app.mas.llm import LLMProviderError, create_provider
from app.mas.orchestrator import list_workflows, run_workflow
from app.mas.planner import plan_analysis
from app.mas.rag_embedding import EmbeddingProviderError, create_embedding
from app.mas.rag_service import (
    create_document,
    delete_document,
    index_document,
    list_documents,
    read_document,
    reindex_document,
    search_knowledge,
)
from app.mas.rag_vectorstore import VectorStoreError, create_vectorstore
from app.mas.schemas import (
    EvidenceLLMContext,
    EvidencePack,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    LLMHealthResponse,
    LLMProviderInfo,
    LLMStructuredRequest,
    LLMStructuredResponse,
    LLMTextRequest,
    LLMTextResponse,
    MasAgentRunCreate,
    MasAgentRunRead,
    MasEvidenceBundleResponse,
    MasEvidenceItemCreate,
    MasEvidenceItemRead,
    MasModelCallCreate,
    MasModelCallRead,
    MasRunCreate,
    MasRunDetailResponse,
    MasRunListResponse,
    MasRunRead,
    MasRunStatusUpdate,
    MasRunSummary,
    MasToolCallCreate,
    MasToolCallRead,
    MasToolCallsResponse,
    MasWorkflowRequest,
    MasWorkflowResponse,
    PlannerInput,
    PlannerResponse,
    RagDeleteResponse,
    RagHealthResponse,
    RagIndexJobRead,
    RagSearchRequest,
    RagSearchResponse,
    SynthesisInput,
    SynthesisResponse,
    ToolContext,
    ToolListResponse,
    ToolResult,
    ToolRunRequest,
)
from app.mas.service import (
    add_agent_run,
    add_evidence_item,
    add_model_call,
    add_tool_call,
    create_run,
    list_evidence,
    list_model_calls,
    list_tool_calls,
    read_run,
    update_status,
)
from app.mas.synthesis import run_synthesis
from app.mas.tools import create_registry
from app.models.tables import KnowledgeDocument, MasRun

router = APIRouter(prefix='/mas', tags=['mas'])
SESSION_DEPENDENCY = Depends(get_session)
DATE_FROM_QUERY = Query(default=None)
DATE_TO_QUERY = Query(default=None)


def project_id() -> UUID:
    """Resolve default project identifier.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    return resolve_project(None, settings.default_project_id)


def require_run(session: Session, run_id: UUID) -> MasRun:
    """Read required MAS run.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    record = read_run(session, project_id(), run_id)
    if record is None:
        raise HTTPException(status_code=404, detail='MAS run was not found')
    return record


def require_document(session: Session, document_id: UUID) -> KnowledgeDocument:
    """Read required knowledge document.
    Args:
        session (Session): Active database session.
        document_id (UUID): Knowledge document identifier."""
    record = read_document(session, project_id(), document_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Knowledge document was not found')
    return record


def ensure_tool_run(session: Session, request: ToolRunRequest, tool_name: str) -> MasRun:
    """Ensure MAS run for tool execution.
    Args:
        session (Session): Active database session.
        request (ToolRunRequest): Tool run request.
        tool_name (str): Tool name."""
    if request.mas_run_id is not None:
        return require_run(session, request.mas_run_id)
    run_request = MasRunCreate(
        user_query=f'Debug tool run: {tool_name}',
        resolved_intent='tool_debug',
        resolved_context_json=request.context.model_dump(mode='json'),
        strategy_mode=request.context.strategy_mode,
        country_id=request.context.country_id,
        company_id=request.context.company_id,
        date_from=request.context.date_from,
        date_to=request.context.date_to,
        budget_amount=request.context.budget_amount,
        currency=request.context.currency,
    )
    settings = get_settings()
    return create_run(session, project_id(), run_request, settings.llm_provider, settings.llm_model)


@router.post('/runs', response_model=MasWorkflowResponse)
def create_mas_run(
    request: MasWorkflowRequest,
    session: Session = SESSION_DEPENDENCY,
) -> MasWorkflowResponse:
    """Create and run MAS workflow.
    Args:
        request (MasWorkflowRequest): MAS workflow request.
        session (Session): Active database session."""
    try:
        return run_workflow(session, get_settings(), request)
    except LLMProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get('/runs', response_model=MasRunListResponse)
def read_mas_runs(
    session: Session = SESSION_DEPENDENCY,
    status: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    strategy_mode: str | None = Query(default=None),
    country: str | None = Query(default=None),
    company: str | None = Query(default=None),
    date_from: date | None = DATE_FROM_QUERY,
    date_to: date | None = DATE_TO_QUERY,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> MasRunListResponse:
    """Read MAS runs.
    Args:
        session (Session): Active database session.
        status (str | None): Optional status filter.
        intent (str | None): Optional intent filter.
        strategy_mode (str | None): Optional strategy mode filter.
        country (str | None): Optional country filter.
        company (str | None): Optional company filter.
        date_from (date | None): Optional created from date.
        date_to (date | None): Optional created to date.
        limit (int): Result limit.
        offset (int): Result offset."""
    items, total = list_workflows(
        session,
        project_id(),
        status,
        intent,
        strategy_mode,
        country,
        company,
        date_from,
        date_to,
        limit,
        offset,
    )
    return MasRunListResponse(items=[build_summary(item) for item in items], total=total)


@router.post('/runs/{run_id}/status', response_model=MasRunRead)
def update_mas_status(
    run_id: UUID,
    request: MasRunStatusUpdate,
    session: Session = SESSION_DEPENDENCY,
) -> MasRunRead:
    """Update MAS run status.
    Args:
        run_id (UUID): MAS run identifier.
        request (MasRunStatusUpdate): Status update payload.
        session (Session): Active database session."""
    record = require_run(session, run_id)
    return update_status(session, record, request)


@router.post('/runs/{run_id}/agent-runs', response_model=MasAgentRunRead)
def create_agent_run(
    run_id: UUID,
    request: MasAgentRunCreate,
    session: Session = SESSION_DEPENDENCY,
) -> MasAgentRunRead:
    """Create MAS agent run.
    Args:
        run_id (UUID): MAS run identifier.
        request (MasAgentRunCreate): Agent run create payload.
        session (Session): Active database session."""
    require_run(session, run_id)
    return add_agent_run(session, run_id, request)


@router.post('/runs/{run_id}/tool-calls', response_model=MasToolCallRead)
def create_tool_call(
    run_id: UUID,
    request: MasToolCallCreate,
    session: Session = SESSION_DEPENDENCY,
) -> MasToolCallRead:
    """Create MAS tool call.
    Args:
        run_id (UUID): MAS run identifier.
        request (MasToolCallCreate): Tool call create payload.
        session (Session): Active database session."""
    require_run(session, run_id)
    return add_tool_call(session, run_id, request)


@router.get('/runs/{run_id}/tool-calls', response_model=MasToolCallsResponse)
def read_tool_calls(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> MasToolCallsResponse:
    """Read MAS tool calls.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    require_run(session, run_id)
    return MasToolCallsResponse(mas_run_id=run_id, tool_calls=list_tool_calls(session, run_id))


@router.get('/runs/{run_id}/model-calls', response_model=list[MasModelCallRead])
def read_model_calls(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> list[MasModelCallRead]:
    """Read MAS model calls.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    require_run(session, run_id)
    return list_model_calls(session, run_id)


@router.post('/runs/{run_id}/llm/text', response_model=LLMTextResponse)
def generate_text(
    run_id: UUID,
    request: LLMTextRequest,
    session: Session = SESSION_DEPENDENCY,
) -> LLMTextResponse:
    """Generate LLM text.
    Args:
        run_id (UUID): MAS run identifier.
        request (LLMTextRequest): LLM text request.
        session (Session): Active database session."""
    require_run(session, run_id)
    settings = get_settings()
    try:
        provider = create_provider(settings)
        response = provider.generate_text(
            request.system_prompt,
            request.user_prompt,
            request.context,
            request.temperature,
            request.max_tokens,
        )
    except LLMProviderError as error:
        add_model_call(
            session,
            run_id,
            build_failed_call(request, settings.llm_provider, settings.llm_model, str(error)),
        )
        raise HTTPException(status_code=503, detail=str(error)) from error
    add_model_call(session, run_id, build_text_call(request, response, settings))
    return response


@router.post('/runs/{run_id}/llm/structured', response_model=LLMStructuredResponse)
def generate_structured(
    run_id: UUID,
    request: LLMStructuredRequest,
    session: Session = SESSION_DEPENDENCY,
) -> LLMStructuredResponse:
    """Generate LLM structured output.
    Args:
        run_id (UUID): MAS run identifier.
        request (LLMStructuredRequest): LLM structured request.
        session (Session): Active database session."""
    require_run(session, run_id)
    settings = get_settings()
    try:
        provider = create_provider(settings)
        response = provider.generate_structured(
            request.system_prompt,
            request.user_prompt,
            request.output_schema,
            request.context,
            request.temperature,
            request.max_tokens,
        )
    except LLMProviderError as error:
        add_model_call(
            session,
            run_id,
            build_failed_call(request, settings.llm_provider, settings.llm_model, str(error), True),
        )
        raise HTTPException(status_code=503, detail=str(error)) from error
    add_model_call(session, run_id, build_structured_call(request, response, settings))
    return response


@router.get('/tools', response_model=ToolListResponse)
def read_tools() -> ToolListResponse:
    """Read MAS tools.
    Args:
        None (None): No arguments are required."""
    registry = create_registry()
    return ToolListResponse(items=registry.list_tools())


@router.post('/tools/{tool_name}/run', response_model=ToolResult)
def run_tool(
    tool_name: str,
    request: ToolRunRequest,
    session: Session = SESSION_DEPENDENCY,
) -> ToolResult:
    """Run MAS tool.
    Args:
        tool_name (str): Tool name.
        request (ToolRunRequest): Tool run request.
        session (Session): Active database session."""
    registry = create_registry()
    tool = registry.get_tool(tool_name)
    if tool is None:
        raise HTTPException(status_code=404, detail='MAS tool was not found')
    record = ensure_tool_run(session, request, tool_name)
    context = enrich_context(request.context, record.project_id)
    result = tool.run(session, get_settings(), context, request.parameters)
    persist_tool_result(session, record.id, request, result)
    if request.save_evidence and result.status in {'success', 'partial'}:
        persist_tool_evidence(session, record.id, result)
    return result


@router.post('/planner/plan', response_model=PlannerResponse)
def plan_mas_analysis(
    request: PlannerInput,
    session: Session = SESSION_DEPENDENCY,
) -> PlannerResponse:
    """Plan MAS analysis.
    Args:
        request (PlannerInput): Planner input.
        session (Session): Active database session."""
    try:
        return plan_analysis(session, get_settings(), request)
    except LLMProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post('/synthesis/run', response_model=SynthesisResponse)
def run_synthesis_debug(
    request: SynthesisInput,
    session: Session = SESSION_DEPENDENCY,
) -> SynthesisResponse:
    """Run synthesis debug endpoint.
    Args:
        request (SynthesisInput): Synthesis input.
        session (Session): Active database session."""
    require_run(session, request.mas_run_id)
    try:
        return run_synthesis(session, get_settings(), request)
    except LLMProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post('/runs/{run_id}/synthesis', response_model=SynthesisResponse)
def run_mas_synthesis(
    run_id: UUID,
    request: SynthesisInput | None = None,
    session: Session = SESSION_DEPENDENCY,
) -> SynthesisResponse:
    """Run MAS synthesis.
    Args:
        run_id (UUID): MAS run identifier.
        request (SynthesisInput | None): Optional synthesis input.
        session (Session): Active database session."""
    require_run(session, run_id)
    synthesis_request = request or SynthesisInput(mas_run_id=run_id)
    synthesis_request.mas_run_id = run_id
    try:
        response = run_synthesis(session, get_settings(), synthesis_request)
        record = require_run(session, run_id)
        try:
            build_history(session, record)
        except Exception:
            session.rollback()
        return response
    except LLMProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post('/runs/{run_id}/evidence', response_model=MasEvidenceItemRead)
def create_evidence(
    run_id: UUID,
    request: MasEvidenceItemCreate,
    session: Session = SESSION_DEPENDENCY,
) -> MasEvidenceItemRead:
    """Create MAS evidence item.
    Args:
        run_id (UUID): MAS run identifier.
        request (MasEvidenceItemCreate): Evidence item create payload.
        session (Session): Active database session."""
    require_run(session, run_id)
    return add_evidence_item(session, run_id, request)


@router.get('/runs/{run_id}/evidence', response_model=MasEvidenceBundleResponse)
def read_evidence(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> MasEvidenceBundleResponse:
    """Read MAS evidence items.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    require_run(session, run_id)
    pack = read_latest_pack(session, run_id)
    return MasEvidenceBundleResponse(
        mas_run_id=run_id,
        evidence_items=list_evidence(session, run_id),
        evidence_pack=pack.pack_json if pack is not None else None,
        llm_context=pack.llm_context_json if pack is not None else None,
    )


@router.get('/runs/{run_id}/evidence-pack', response_model=EvidencePack)
def read_evidence_pack(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> EvidencePack:
    """Read evidence pack.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    record = require_run(session, run_id)
    pack = read_latest_pack(session, run_id)
    if pack is None:
        pack = build_pack(session, record)
    return EvidencePack.model_validate(pack.pack_json)


@router.post('/runs/{run_id}/evidence-pack/rebuild', response_model=EvidencePack)
def rebuild_evidence_pack(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> EvidencePack:
    """Rebuild evidence pack.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    record = require_run(session, run_id)
    pack = build_pack(session, record)
    return EvidencePack.model_validate(pack.pack_json)


@router.get('/runs/{run_id}/llm-context', response_model=EvidenceLLMContext)
def read_llm_context(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> EvidenceLLMContext:
    """Read LLM context.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    record = require_run(session, run_id)
    pack = read_latest_pack(session, run_id)
    if pack is None:
        pack = build_pack(session, record)
    return EvidenceLLMContext.model_validate(pack.llm_context_json)


@router.get('/llm/provider', response_model=LLMProviderInfo)
def read_llm_provider() -> LLMProviderInfo:
    """Read LLM provider.
    Args:
        None (None): No arguments are required."""
    try:
        provider = create_provider(get_settings())
    except LLMProviderError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return provider.get_provider_info()


@router.get('/llm/health', response_model=LLMHealthResponse)
def read_llm_health() -> LLMHealthResponse:
    """Read LLM health.
    Args:
        None (None): No arguments are required."""
    try:
        provider = create_provider(get_settings())
    except LLMProviderError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return provider.health_check()


@router.get('/rag/health', response_model=RagHealthResponse)
def read_rag_health() -> RagHealthResponse:
    """Read RAG health.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    try:
        vectorstore_health = create_vectorstore(settings).health_check()
    except VectorStoreError as error:
        vectorstore_health = None
        vectorstore_message = str(error)
    else:
        vectorstore_message = vectorstore_health.message
    try:
        embedding_health = create_embedding(settings).health_check()
    except EmbeddingProviderError as error:
        embedding_health = None
        embedding_message = str(error)
    else:
        embedding_message = embedding_health.message
    return build_rag_health(settings, vectorstore_health, embedding_health, vectorstore_message, embedding_message)


@router.post('/rag/documents', response_model=KnowledgeDocumentRead)
def create_rag_document(
    request: KnowledgeDocumentCreate,
    session: Session = SESSION_DEPENDENCY,
) -> KnowledgeDocumentRead:
    """Create RAG document.
    Args:
        request (KnowledgeDocumentCreate): Knowledge document create payload.
        session (Session): Active database session."""
    return create_document(session, project_id(), request)


@router.get('/rag/documents', response_model=list[KnowledgeDocumentRead])
def read_rag_documents(
    session: Session = SESSION_DEPENDENCY,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[KnowledgeDocumentRead]:
    """Read RAG documents.
    Args:
        session (Session): Active database session.
        limit (int): Result limit."""
    return list_documents(session, project_id(), limit)


@router.post('/rag/documents/{document_id}/index', response_model=RagIndexJobRead)
def index_rag_document(
    document_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> RagIndexJobRead:
    """Index RAG document.
    Args:
        document_id (UUID): Knowledge document identifier.
        session (Session): Active database session."""
    document = require_document(session, document_id)
    return index_document(session, document, get_settings())


@router.post('/rag/documents/{document_id}/reindex', response_model=RagIndexJobRead)
def reindex_rag_document(
    document_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> RagIndexJobRead:
    """Reindex RAG document.
    Args:
        document_id (UUID): Knowledge document identifier.
        session (Session): Active database session."""
    document = require_document(session, document_id)
    return reindex_document(session, document, get_settings())


@router.delete('/rag/documents/{document_id}/index', response_model=RagDeleteResponse)
def delete_rag_index(
    document_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> RagDeleteResponse:
    """Delete RAG index.
    Args:
        document_id (UUID): Knowledge document identifier.
        session (Session): Active database session."""
    document = require_document(session, document_id)
    return delete_document(session, document, get_settings())


@router.post('/rag/search', response_model=RagSearchResponse)
def search_rag(
    request: RagSearchRequest,
    session: Session = SESSION_DEPENDENCY,
) -> RagSearchResponse:
    """Search RAG knowledge.
    Args:
        request (RagSearchRequest): RAG search request.
        session (Session): Active database session."""
    if request.mas_run_id is not None:
        require_run(session, request.mas_run_id)
    try:
        return search_knowledge(session, project_id(), request, get_settings())
    except (EmbeddingProviderError, VectorStoreError) as error:
        mark_rag_failed(session, request.mas_run_id, str(error))
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get('/runs/{run_id}', response_model=MasRunDetailResponse)
def read_mas_run(
    run_id: UUID,
    session: Session = SESSION_DEPENDENCY,
) -> MasRunDetailResponse:
    """Read MAS run.
    Args:
        run_id (UUID): MAS run identifier.
        session (Session): Active database session."""
    return build_detail(session, require_run(session, run_id))


def build_summary(record: MasRun) -> MasRunSummary:
    """Build MAS run summary.
    Args:
        record (MasRun): MAS run record."""
    context = record.resolved_context_json or {}
    return MasRunSummary(
        id=record.id,
        project_id=record.project_id,
        status=record.status,
        user_query=record.user_query,
        resolved_intent=record.resolved_intent,
        resolved_context_json=context,
        strategy_mode=record.strategy_mode,
        country=read_context_value(context, 'country'),
        company=read_context_value(context, 'company'),
        final_summary=record.final_summary,
        date_from=record.date_from,
        date_to=record.date_to,
        rag_status=record.rag_status,
        rag_results_count=record.rag_results_count,
        completed_at=record.completed_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def build_detail(session: Session, record: MasRun) -> MasRunDetailResponse:
    """Build MAS run detail.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record."""
    pack = read_latest_pack(session, record.id)
    model_calls = list_model_calls(session, record.id)
    latest_model_call = model_calls[-1] if model_calls else None
    return MasRunDetailResponse(
        mas_run_id=record.id,
        project_id=record.project_id,
        status=record.status,
        user_query=record.user_query,
        resolved_intent=record.resolved_intent,
        resolved_context=record.resolved_context_json or {},
        planner_output_json=record.planner_output_json,
        synthesis_output=record.synthesis_output_json,
        final_answer=record.final_answer,
        final_summary=record.final_summary,
        tool_calls=list_tool_calls(session, record.id),
        evidence_items=list_evidence(session, record.id),
        evidence_pack=pack.pack_json if pack is not None else None,
        llm_context=pack.llm_context_json if pack is not None else None,
        rag_chunks_used=build_rag_chunks(session, record),
        llm_provider=record.default_llm_provider,
        llm_model=record.default_llm_model,
        embedding_provider=get_settings().embedding_provider,
        prompt_version=read_prompt_value(latest_model_call),
        metrics_json=record.metrics_json,
        error_message=record.error_message,
        created_at=record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
    )


def build_rag_chunks(session: Session, record: MasRun) -> list[dict[str, object]]:
    """Build RAG chunk list.
    Args:
        session (Session): Active database session.
        record (MasRun): MAS run record."""
    chunks: list[dict[str, object]] = []
    for evidence_item in list_evidence(session, record.id):
        data = evidence_item.data_json or {}
        chunks.extend(read_rag_results(data))
    if chunks:
        return chunks
    synthesis_output = record.synthesis_output_json or {}
    return read_rag_results(synthesis_output)


def read_rag_results(data: dict[str, object]) -> list[dict[str, object]]:
    """Read RAG results.
    Args:
        data (dict[str, object]): Source payload."""
    results = data.get('results')
    if not isinstance(results, list):
        nested_data = data.get('data')
        if isinstance(nested_data, dict):
            results = nested_data.get('results')
    if not isinstance(results, list):
        return []
    chunks: list[dict[str, object]] = []
    for item in results:
        if isinstance(item, dict):
            chunks.append(
                {
                    'document_id': item.get('document_id'),
                    'chunk_id': item.get('chunk_id'),
                    'title': item.get('title'),
                    'score': item.get('score'),
                }
            )
    return chunks


def read_context_value(context: dict[str, object], key: str) -> str | None:
    """Read context value.
    Args:
        context (dict[str, object]): Context payload.
        key (str): Context key."""
    value = context.get(key)
    if value is None:
        return None
    return str(value)


def read_prompt_value(model_call: MasModelCallRead | None) -> str | None:
    """Read prompt value.
    Args:
        model_call (MasModelCallRead | None): MAS model call."""
    if model_call is None:
        return None
    if model_call.prompt_key is None:
        return None
    return f'{model_call.prompt_key}:{model_call.prompt_version_id}'


def mark_rag_failed(session: Session, run_id: UUID | None, error_message: str) -> MasRun | None:
    """Mark RAG failed.
    Args:
        session (Session): Active database session.
        run_id (UUID | None): MAS run identifier.
        error_message (str): Error message."""
    if run_id is None:
        return None
    record = session.get(MasRun, run_id)
    if record is None:
        return None
    record.rag_enabled = True
    record.rag_status = 'failed'
    record.error_message = error_message
    session.commit()
    session.refresh(record)
    return record


def build_rag_health(
    settings: Settings,
    vectorstore_health: object,
    embedding_health: object,
    vectorstore_message: str | None,
    embedding_message: str | None,
) -> RagHealthResponse:
    """Build RAG health response.
    Args:
        settings (Settings): Application settings.
        vectorstore_health (object): Vector store health.
        embedding_health (object): Embedding health.
        vectorstore_message (str | None): Vector store message.
        embedding_message (str | None): Embedding message."""
    vectorstore_available = bool(getattr(vectorstore_health, 'is_available', False))
    embedding_available = bool(getattr(embedding_health, 'is_available', False))
    message = vectorstore_message or embedding_message
    return RagHealthResponse(
        vectorstore_provider=settings.vectorstore_provider,
        available=vectorstore_available and embedding_available,
        collection=settings.qdrant_collection,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dimensions=settings.embedding_dimensions,
        vectorstore_status=str(getattr(vectorstore_health, 'status', 'failed')),
        embedding_status=str(getattr(embedding_health, 'status', 'failed')),
        message=message,
    )


def enrich_context(context: ToolContext, run_project_id: UUID) -> ToolContext:
    """Enrich tool context.
    Args:
        context (ToolContext): Tool context.
        run_project_id (UUID): MAS run project identifier."""
    data = context.model_dump()
    data['project_id'] = context.project_id or run_project_id
    return ToolContext(**data)


def persist_tool_result(session: Session, run_id: UUID, request: ToolRunRequest, result: ToolResult) -> MasToolCallRead:
    """Persist tool result.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (ToolRunRequest): Tool run request.
        result (ToolResult): Tool result."""
    tool_request = MasToolCallCreate(
        tool_name=result.tool_name,
        tool_type='retrieval' if result.tool_name == 'rag_retrieval' else 'analytics',
        status=tool_status(result.status),
        input_json=request.model_dump(mode='json'),
        output_json=result.model_dump(mode='json'),
        error_message='; '.join(result.errors) if result.errors else None,
    )
    return add_tool_call(session, run_id, tool_request)


def persist_tool_evidence(session: Session, run_id: UUID, result: ToolResult) -> MasEvidenceItemRead:
    """Persist tool evidence.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        result (ToolResult): Tool result."""
    evidence_request = MasEvidenceItemCreate(
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
    return add_evidence_item(session, run_id, evidence_request)


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


def request_temperature(request: LLMTextRequest) -> Decimal:
    """Build request temperature.
    Args:
        request (LLMTextRequest): LLM request."""
    settings = get_settings()
    temperature = request.temperature if request.temperature is not None else settings.llm_temperature
    return Decimal(str(temperature))


def request_tokens(request: LLMTextRequest) -> int:
    """Build request max tokens.
    Args:
        request (LLMTextRequest): LLM request."""
    settings = get_settings()
    return request.max_tokens if request.max_tokens is not None else settings.llm_max_tokens


def build_text_call(request: LLMTextRequest, response: LLMTextResponse, settings: Settings) -> MasModelCallCreate:
    """Build text model call.
    Args:
        request (LLMTextRequest): LLM request.
        response (LLMTextResponse): LLM response.
        settings (Settings): Application settings."""
    return MasModelCallCreate(
        agent_run_id=request.agent_run_id,
        prompt_version_id=request.prompt_version_id,
        prompt_key=request.prompt_key,
        provider=response.provider,
        model_name=response.model,
        temperature=request_temperature(request),
        max_tokens=request_tokens(request),
        structured_output_enabled=False,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        total_tokens=response.usage.total_tokens,
        estimated_cost=response.usage.estimated_cost,
        latency_ms=response.latency_ms,
        status='completed',
        raw_response_json={'text': response.text, 'settings_provider': getattr(settings, 'llm_provider', None)},
    )


def build_structured_call(
    request: LLMStructuredRequest,
    response: LLMStructuredResponse,
    settings: Settings,
) -> MasModelCallCreate:
    """Build structured model call.
    Args:
        request (LLMStructuredRequest): LLM request.
        response (LLMStructuredResponse): LLM response.
        settings (Settings): Application settings."""
    return MasModelCallCreate(
        agent_run_id=request.agent_run_id,
        prompt_version_id=request.prompt_version_id,
        prompt_key=request.prompt_key,
        provider=response.provider,
        model_name=response.model,
        temperature=request_temperature(request),
        max_tokens=request_tokens(request),
        structured_output_enabled=True,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        total_tokens=response.usage.total_tokens,
        estimated_cost=response.usage.estimated_cost,
        latency_ms=response.latency_ms,
        status='completed',
        raw_response_json={
            'raw_text': response.raw_text,
            'parsed_json': response.parsed_json,
            'validation_status': response.validation_status,
            'settings_provider': getattr(settings, 'llm_provider', None),
        },
    )


def build_failed_call(
    request: LLMTextRequest,
    provider: str,
    model_name: str,
    error_message: str,
    structured_output_enabled: bool = False,
) -> MasModelCallCreate:
    """Build failed model call.
    Args:
        request (LLMTextRequest): LLM request.
        provider (str): Provider name.
        model_name (str): Model name.
        error_message (str): Error message.
        structured_output_enabled (bool): Whether structured output was requested."""
    return MasModelCallCreate(
        agent_run_id=request.agent_run_id,
        prompt_version_id=request.prompt_version_id,
        prompt_key=request.prompt_key,
        provider=provider,
        model_name=model_name,
        temperature=request_temperature(request),
        max_tokens=request_tokens(request),
        structured_output_enabled=structured_output_enabled,
        status='failed',
        error_message=error_message,
    )
