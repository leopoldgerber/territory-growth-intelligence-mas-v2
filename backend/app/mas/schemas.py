from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

MasRunStatus = Literal[
    'pending',
    'running',
    'needs_clarification',
    'completed',
    'partial',
    'failed',
    'skipped',
    'cancelled',
]
MasRunMode = Literal['sync', 'async']
MasAgentType = Literal['llm', 'tool', 'rule_based', 'retrieval', 'synthesis']
MasToolType = Literal['analytics', 'report', 'database', 'retrieval', 'orchestrator', 'external']
LLMProviderName = Literal['openai', 'ollama', 'disabled']
LLMCallStatus = Literal['completed', 'failed']
EmbeddingProviderName = Literal['openai', 'ollama', 'disabled']
VectorStoreProviderName = Literal['qdrant', 'disabled']
KnowledgeDocumentType = Literal[
    'methodology',
    'budget_strategy_summary',
    'mas_run_summary',
    'insight',
    'feedback',
]
KnowledgeSourceType = Literal[
    'methodology_doc',
    'budget_strategy',
    'mas_run',
    'user_note',
]
KnowledgeDocumentStatus = Literal['draft', 'ready', 'indexed', 'index_failed', 'archived']
RagJobStatus = Literal['pending', 'running', 'completed', 'failed']
MasToolStatus = Literal['success', 'partial', 'failed', 'skipped']
MasToolConfidence = Literal['high', 'medium', 'low', 'unknown']
MasToolSource = Literal[
    'analytics_db',
    'derived_signal',
    'opportunity_score',
    'budget_strategy_report',
    'rag',
    'report',
    'system',
]
EvidencePackConfidence = Literal['high', 'medium', 'low', 'unknown']
EvidencePackCompleteness = Literal['complete', 'partial', 'insufficient']
MasSourceType = Literal[
    'analytics_db',
    'report',
    'derived_signal',
    'opportunity_score',
    'budget_strategy',
    'rag',
    'user_input',
    'llm_output',
]
MasEvidenceType = Literal[
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
]
MasConfidence = Literal['low', 'medium', 'high']
SynthesisConfidence = Literal['high', 'medium', 'low', 'unknown']
SynthesisPriority = Literal['high', 'medium', 'low']
SynthesisSeverity = Literal['high', 'medium', 'low']


class MasContext(BaseModel):
    project_id: UUID | None = None
    strategy_mode: str | None = None
    country: str | None = None
    company: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    budget_amount: Decimal | None = None
    currency: str | None = None


class MasRunCreate(BaseModel):
    user_query: str = Field(min_length=1)
    created_by: str | None = None
    resolved_intent: str | None = None
    resolved_context_json: dict[str, Any] = Field(default_factory=dict)
    strategy_mode: str | None = None
    country_id: int | None = None
    company_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    budget_amount: Decimal | None = None
    currency: str | None = None
    prompt_version_id: int | None = None


class MasRunStatusUpdate(BaseModel):
    status: MasRunStatus
    planner_output_json: dict[str, Any] | None = None
    synthesis_output_json: dict[str, Any] | None = None
    metrics_json: dict[str, Any] | None = None
    final_answer: str | None = None
    final_summary: str | None = None
    error_message: str | None = None


class MasAgentRunCreate(BaseModel):
    agent_name: str
    agent_type: MasAgentType
    status: MasRunStatus = 'pending'
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] | None = None
    error_message: str | None = None


class MasToolCallCreate(BaseModel):
    agent_run_id: UUID | None = None
    tool_name: str
    tool_type: MasToolType
    status: MasRunStatus = 'pending'
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] | None = None
    error_message: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)


class MasEvidenceItemCreate(BaseModel):
    source_type: MasSourceType
    evidence_type: MasEvidenceType
    source_table: str | None = None
    source_record_id: str | None = None
    context_hash: str | None = None
    title: str
    summary: str
    data_json: dict[str, Any] = Field(default_factory=dict)
    confidence: MasConfidence = 'medium'


class MasAgentRunRead(BaseModel):
    id: UUID
    mas_run_id: UUID
    agent_name: str
    agent_type: str
    status: str
    input_json: dict[str, Any]
    output_json: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {'from_attributes': True}


class MasToolCallRead(BaseModel):
    id: UUID
    mas_run_id: UUID
    agent_run_id: UUID | None
    tool_name: str
    tool_type: str
    status: str
    input_json: dict[str, Any]
    output_json: dict[str, Any] | None
    error_message: str | None
    duration_ms: int | None
    created_at: datetime

    model_config = {'from_attributes': True}


class MasEvidenceItemRead(BaseModel):
    id: UUID
    mas_run_id: UUID
    source_type: str
    evidence_type: str
    source_table: str | None
    source_record_id: str | None
    context_hash: str | None
    title: str
    summary: str
    data_json: dict[str, Any]
    confidence: str
    created_at: datetime

    model_config = {'from_attributes': True}


class MasRunRead(BaseModel):
    id: UUID
    project_id: UUID
    created_by: str | None
    status: str
    user_query: str
    resolved_intent: str | None
    resolved_context_json: dict[str, Any]
    strategy_mode: str | None
    country_id: int | None
    company_id: int | None
    date_from: date | None
    date_to: date | None
    budget_amount: Decimal | None
    currency: str | None
    default_llm_provider: str | None
    default_llm_model: str | None
    prompt_version_id: int | None
    rag_enabled: bool
    rag_status: str | None
    rag_results_count: int
    planner_output_json: dict[str, Any] | None
    synthesis_output_json: dict[str, Any] | None
    metrics_json: dict[str, Any] | None
    final_answer: str | None
    final_summary: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class MasRunSummary(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    user_query: str
    resolved_intent: str | None
    resolved_context_json: dict[str, Any]
    strategy_mode: str | None
    country: str | None = None
    company: str | None = None
    final_summary: str | None = None
    date_from: date | None
    date_to: date | None
    rag_status: str | None
    rag_results_count: int
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class MasRunListResponse(BaseModel):
    items: list[MasRunSummary]
    total: int = 0


class MasPromptVersionRead(BaseModel):
    id: int
    prompt_key: str
    version: str
    description: str | None
    system_prompt: str | None
    user_prompt_template: str | None
    output_schema_json: dict[str, Any] | None
    is_active: bool
    created_at: datetime

    model_config = {'from_attributes': True}


class LLMUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: Decimal | None = None


class LLMTextRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    context: dict[str, Any] = Field(default_factory=dict)
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    prompt_key: str | None = None
    prompt_version_id: int | None = None
    agent_run_id: UUID | None = None


class LLMStructuredRequest(LLMTextRequest):
    output_schema: dict[str, Any] = Field(default_factory=dict)


class LLMTextResponse(BaseModel):
    text: str
    usage: LLMUsage
    provider: str
    model: str
    latency_ms: int


class LLMStructuredResponse(BaseModel):
    parsed_json: dict[str, Any] | None
    raw_text: str
    validation_status: str
    usage: LLMUsage
    provider: str
    model: str
    latency_ms: int


class LLMProviderInfo(BaseModel):
    provider: str
    model: str
    structured_output_supported: bool
    is_available: bool


class LLMHealthResponse(LLMProviderInfo):
    status: str
    message: str | None = None


class MasModelCallCreate(BaseModel):
    agent_run_id: UUID | None = None
    prompt_version_id: int | None = None
    prompt_key: str | None = None
    provider: str
    model_name: str
    temperature: Decimal | None = None
    max_tokens: int | None = None
    structured_output_enabled: bool = False
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: Decimal | None = None
    latency_ms: int | None = None
    status: LLMCallStatus
    error_message: str | None = None
    raw_response_json: dict[str, Any] | None = None


class MasModelCallRead(BaseModel):
    id: UUID
    mas_run_id: UUID
    agent_run_id: UUID | None
    prompt_version_id: int | None
    prompt_key: str | None
    provider: str
    model_name: str
    temperature: Decimal | None
    max_tokens: int | None
    structured_output_enabled: bool
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    estimated_cost: Decimal | None
    latency_ms: int | None
    status: str
    error_message: str | None
    raw_response_json: dict[str, Any] | None
    created_at: datetime

    model_config = {'from_attributes': True}


class EmbeddingModelInfo(BaseModel):
    provider: str
    model: str
    dimensions: int
    is_available: bool


class EmbeddingHealthResponse(EmbeddingModelInfo):
    status: str
    message: str | None = None


class VectorStoreInfo(BaseModel):
    provider: str
    collection: str
    is_available: bool


class VectorStoreHealthResponse(VectorStoreInfo):
    status: str
    message: str | None = None


class RagHealthResponse(BaseModel):
    vectorstore_provider: str
    available: bool
    collection: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    vectorstore_status: str
    embedding_status: str
    message: str | None = None


class KnowledgeDocumentCreate(BaseModel):
    document_type: KnowledgeDocumentType
    source_type: KnowledgeSourceType
    source_record_id: str | None = None
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    status: KnowledgeDocumentStatus = 'ready'
    version: str = 'v1'


class KnowledgeDocumentRead(BaseModel):
    id: UUID
    project_id: UUID
    document_type: str
    source_type: str
    source_record_id: str | None
    title: str
    content: str
    metadata_json: dict[str, Any]
    status: str
    version: str
    indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class KnowledgeChunkRead(BaseModel):
    id: UUID
    document_id: UUID
    project_id: UUID
    chunk_index: int
    content: str
    content_hash: str
    metadata_json: dict[str, Any]
    qdrant_point_id: str | None
    embedding_provider: str | None
    embedding_model: str | None
    embedding_dimensions: int | None
    indexed_at: datetime | None
    created_at: datetime

    model_config = {'from_attributes': True}


class RagIndexJobRead(BaseModel):
    id: UUID
    project_id: UUID
    document_id: UUID
    status: str
    chunks_count: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {'from_attributes': True}


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mas_run_id: UUID | None = None
    country: str | None = None
    company: str | None = None
    strategy_mode: str | None = None
    document_types: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    create_evidence_items: bool = False


class RagSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    document_type: str | None = None
    title: str | None = None
    content: str
    metadata: dict[str, Any]


class RagSearchResponse(BaseModel):
    results: list[RagSearchResult]
    provider: str
    collection: str
    latency_ms: int
    filters_json: dict[str, Any]


class RagDeleteResponse(BaseModel):
    document_id: UUID
    deleted_chunks: int
    status: str


class ToolSourceRef(BaseModel):
    source_type: str
    source_name: str
    record_id: str | None = None
    context_hash: str | None = None


class ToolContext(BaseModel):
    project_id: UUID | None = None
    strategy_mode: str | None = None
    country_id: int | None = None
    country_code: str | None = None
    country_name: str | None = None
    company_id: int | None = None
    company_name: str | None = None
    company_domain: str | None = None
    competitors: list[str] = Field(default_factory=list)
    competitor_domains: list[str] = Field(default_factory=list)
    tld: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    budget_amount: Decimal | None = None
    currency: str | None = None
    context_hash: str | None = None
    calculation_version: str = 'v1'


class ToolResult(BaseModel):
    tool_name: str
    status: MasToolStatus
    evidence_type: str
    source: str
    context: ToolContext
    data: dict[str, Any] | None
    summary: str
    confidence: MasToolConfidence
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    source_refs: list[ToolSourceRef] = Field(default_factory=list)
    created_at: datetime


class ToolRunRequest(BaseModel):
    context: ToolContext
    mas_run_id: UUID | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    save_evidence: bool = True


class ToolInfo(BaseModel):
    tool_name: str
    evidence_type: str
    source: str
    description: str


class ToolListResponse(BaseModel):
    items: list[ToolInfo]


class EvidenceSourceRef(BaseModel):
    evidence_item_id: UUID | None = None
    tool_call_id: UUID | None = None
    source_type: str
    source_table: str | None = None
    source_report_id: str | None = None


class EvidencePackItem(BaseModel):
    id: UUID
    type: str
    source: str
    source_table: str | None = None
    source_record_id: str | None = None
    source_report_id: str | None = None
    tool_call_id: UUID | None = None
    context_hash: str | None = None
    created_at: datetime
    confidence: str
    summary: str
    data: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_ref: EvidenceSourceRef


class MissingEvidenceItem(BaseModel):
    type: str
    reason: str
    severity: str


class FailedEvidenceItem(BaseModel):
    tool_name: str
    evidence_type: str
    error: str
    severity: str


class EvidenceQuality(BaseModel):
    overall_confidence: EvidencePackConfidence
    completeness: EvidencePackCompleteness
    critical_gaps: list[MissingEvidenceItem] = Field(default_factory=list)


class EvidenceSections(BaseModel):
    country: list[EvidencePackItem] = Field(default_factory=list)
    competitors: list[EvidencePackItem] = Field(default_factory=list)
    channels: list[EvidencePackItem] = Field(default_factory=list)
    devices: list[EvidencePackItem] = Field(default_factory=list)
    signals: list[EvidencePackItem] = Field(default_factory=list)
    opportunity_score: list[EvidencePackItem] = Field(default_factory=list)
    budget_strategy: list[EvidencePackItem] = Field(default_factory=list)
    company_profile: list[EvidencePackItem] = Field(default_factory=list)
    rag: list[EvidencePackItem] = Field(default_factory=list)


class EvidenceResolvedContext(BaseModel):
    project_id: UUID
    country: str | None = None
    company: str | None = None
    period: dict[str, date | None]
    strategy_mode: str | None = None
    budget_amount: Decimal | None = None
    currency: str | None = None
    context_hash: str | None = None


class EvidencePack(BaseModel):
    pack_id: UUID
    mas_run_id: UUID
    query: str
    resolved_context: EvidenceResolvedContext
    evidence: EvidenceSections
    warnings: list[str] = Field(default_factory=list)
    missing_evidence: list[MissingEvidenceItem] = Field(default_factory=list)
    failed_evidence: list[FailedEvidenceItem] = Field(default_factory=list)
    evidence_quality: EvidenceQuality
    evidence_priority: list[str] = Field(default_factory=list)
    created_at: datetime


class LLMContextItem(BaseModel):
    type: str
    summary: str
    confidence: str
    source_ref: str
    key_data: dict[str, Any] = Field(default_factory=dict)


class EvidenceLLMContext(BaseModel):
    context: EvidenceResolvedContext
    key_evidence: list[LLMContextItem]
    warnings: list[str]
    missing_evidence: list[MissingEvidenceItem]
    evidence_quality: EvidenceQuality


class EvidencePackRead(BaseModel):
    id: UUID
    mas_run_id: UUID
    context_hash: str | None
    pack_json: dict[str, Any]
    llm_context_json: dict[str, Any]
    quality_json: dict[str, Any]
    created_at: datetime

    model_config = {'from_attributes': True}


class PlannerDefaultContext(BaseModel):
    project_id: UUID | None = None
    strategy_mode: str | None = None
    country: str | None = None
    company: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    budget_amount: Decimal | None = None
    currency: str | None = None
    context_hash: str | None = None


class PlannerAvailableFilters(BaseModel):
    countries: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    strategy_modes: list[str] = Field(default_factory=lambda: ['market_entry', 'existing_presence'])
    currencies: list[str] = Field(default_factory=lambda: ['USD', 'EUR'])


class PlannerInput(BaseModel):
    mas_run_id: UUID | None = None
    query: str = Field(min_length=1)
    default_context: PlannerDefaultContext = Field(default_factory=PlannerDefaultContext)
    available_filters: PlannerAvailableFilters | None = None


class PlannerResolvedContext(BaseModel):
    project_id: UUID | None = None
    country: str | None = None
    company: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    budget_amount: Decimal | None = None
    currency: str | None = None
    context_hash: str | None = None


class AnalysisPlan(BaseModel):
    intent: str
    strategy_mode: str | None = None
    resolved_context: PlannerResolvedContext
    required_tools: list[str] = Field(default_factory=list)
    optional_tools: list[str] = Field(default_factory=list)
    missing_required_inputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
    planning_notes: list[str] = Field(default_factory=list)


class PlannerResponse(BaseModel):
    mas_run_id: UUID
    agent_run_id: UUID
    plan: AnalysisPlan


class MasRunOptions(BaseModel):
    use_rag: bool = True
    save_result: bool = True
    run_mode: MasRunMode = 'sync'


class MasWorkflowRequest(BaseModel):
    project_id: UUID | None = None
    user_query: str = Field(min_length=1)
    default_context: PlannerDefaultContext = Field(default_factory=PlannerDefaultContext)
    options: MasRunOptions = Field(default_factory=MasRunOptions)
    created_by: str | None = None


class MasWorkflowResponse(BaseModel):
    mas_run_id: UUID
    status: str
    resolved_intent: str | None = None
    resolved_context: dict[str, Any] = Field(default_factory=dict)
    final_answer: str | None = None
    final_summary: str | None = None
    confidence: str | None = None
    evidence_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class MasRunDetailResponse(BaseModel):
    mas_run_id: UUID
    project_id: UUID
    status: str
    user_query: str
    resolved_intent: str | None
    resolved_context: dict[str, Any]
    planner_output_json: dict[str, Any] | None
    synthesis_output: dict[str, Any] | None
    final_answer: str | None
    final_summary: str | None
    tool_calls: list[MasToolCallRead]
    evidence_items: list[MasEvidenceItemRead]
    evidence_pack: dict[str, Any] | None = None
    llm_context: dict[str, Any] | None = None
    rag_chunks_used: list[dict[str, Any]] = Field(default_factory=list)
    llm_provider: str | None
    llm_model: str | None
    embedding_provider: str | None = None
    prompt_version: str | None = None
    metrics_json: dict[str, Any] | None = None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class MasEvidenceBundleResponse(BaseModel):
    mas_run_id: UUID
    evidence_items: list[MasEvidenceItemRead]
    evidence_pack: dict[str, Any] | None = None
    llm_context: dict[str, Any] | None = None


class MasToolCallsResponse(BaseModel):
    mas_run_id: UUID
    tool_calls: list[MasToolCallRead]


class SynthesisInput(BaseModel):
    mas_run_id: UUID
    evidence_pack_id: UUID | None = None
    force_rebuild_pack: bool = False
    output_language: str = 'ru'


class SynthesisSection(BaseModel):
    title: str
    content: str
    evidence_refs: list[str] = Field(default_factory=list)


class SynthesisFinding(BaseModel):
    finding: str
    confidence: SynthesisConfidence
    evidence_refs: list[str] = Field(default_factory=list)


class SynthesisRisk(BaseModel):
    risk: str
    severity: SynthesisSeverity
    mitigation: str
    evidence_refs: list[str] = Field(default_factory=list)


class SynthesisAction(BaseModel):
    action: str
    priority: SynthesisPriority
    evidence_refs: list[str] = Field(default_factory=list)


class SynthesisEvidenceUsed(BaseModel):
    evidence_id: str
    type: str
    reason_used: str


class SynthesisOutput(BaseModel):
    answer_type: str
    executive_summary: str
    final_recommendation: str
    reasoning_sections: list[SynthesisSection] = Field(default_factory=list)
    key_findings: list[SynthesisFinding] = Field(default_factory=list)
    risks: list[SynthesisRisk] = Field(default_factory=list)
    recommended_next_actions: list[SynthesisAction] = Field(default_factory=list)
    evidence_used: list[SynthesisEvidenceUsed] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence: SynthesisConfidence


class SynthesisResponse(BaseModel):
    mas_run_id: UUID
    agent_run_id: UUID
    evidence_pack_id: UUID
    synthesis_output: SynthesisOutput
    final_answer_markdown: str
