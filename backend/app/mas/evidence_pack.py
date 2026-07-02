from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.mas.schemas import (
    EvidenceLLMContext,
    EvidencePack,
    EvidencePackItem,
    EvidenceQuality,
    EvidenceResolvedContext,
    EvidenceSections,
    EvidenceSourceRef,
    FailedEvidenceItem,
    LLMContextItem,
    MissingEvidenceItem,
)
from app.models.tables import MasEvidenceItem, MasEvidencePack, MasRun, MasToolCall

PACK_SECTIONS = {
    'country': 'country',
    'competitor': 'competitors',
    'channel': 'channels',
    'device': 'devices',
    'signal': 'signals',
    'opportunity_score': 'opportunity_score',
    'budget_strategy': 'budget_strategy',
    'company_profile': 'company_profile',
    'methodology': 'rag',
    'historical_report': 'rag',
    'insight': 'rag',
}
REQUIRED_BY_INTENT = {
    'market_entry': [
        'country',
        'competitor',
        'channel',
        'device',
        'signal',
        'opportunity_score',
        'budget_strategy',
        'company_profile',
        'methodology',
    ],
    'existing_presence': [
        'country',
        'competitor',
        'channel',
        'device',
        'signal',
        'opportunity_score',
        'budget_strategy',
        'methodology',
    ],
    'general_country_summary': [
        'country',
        'competitor',
        'channel',
        'device',
        'signal',
        'opportunity_score',
    ],
}
EVIDENCE_PRIORITY = [
    'current_analytics',
    'current_reports',
    'methodology',
    'historical_context',
    'user_memory',
]
CRITICAL_TYPES = {'country', 'channel', 'device', 'opportunity_score', 'budget_strategy'}


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def build_pack(session: Session, run: MasRun) -> MasEvidencePack:
    """Build and save evidence pack.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record."""
    evidence_items = read_evidence_items(session, run.id)
    tool_calls = read_tool_calls(session, run.id)
    pack_items = [map_evidence(item, find_tool_call(item, tool_calls)) for item in evidence_items]
    failed_evidence = build_failed(tool_calls)
    sections = group_evidence(pack_items)
    missing_evidence = build_missing(run, sections)
    warnings = collect_warnings(pack_items)
    quality = calculate_quality(pack_items, missing_evidence)
    pack = EvidencePack(
        pack_id=uuid4(),
        mas_run_id=run.id,
        query=run.user_query,
        resolved_context=build_context(run),
        evidence=sections,
        warnings=warnings,
        missing_evidence=missing_evidence,
        failed_evidence=failed_evidence,
        evidence_quality=quality,
        evidence_priority=EVIDENCE_PRIORITY,
        created_at=current_time(),
    )
    validate_pack(pack)
    llm_context = to_llm_context(pack)
    return save_pack(session, run, pack, llm_context)


def read_evidence_items(session: Session, run_id: UUID) -> list[MasEvidenceItem]:
    """Read evidence items.
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


def read_tool_calls(session: Session, run_id: UUID) -> list[MasToolCall]:
    """Read tool calls.
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


def read_latest_pack(session: Session, run_id: UUID) -> MasEvidencePack | None:
    """Read latest evidence pack.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    return session.scalar(
        select(MasEvidencePack)
        .where(MasEvidencePack.mas_run_id == run_id)
        .order_by(MasEvidencePack.created_at.desc())
        .limit(1)
    )


def map_evidence(item: MasEvidenceItem, tool_call: MasToolCall | None) -> EvidencePackItem:
    """Map atomic evidence item.
    Args:
        item (MasEvidenceItem): Atomic evidence item.
        tool_call (MasToolCall | None): Related tool call."""
    data_json = item.data_json or {}
    warnings = read_warnings(data_json)
    source_report_id = read_report_id(item)
    return EvidencePackItem(
        id=item.id,
        type=item.evidence_type,
        source=normalize_source(item.source_type),
        source_table=item.source_table,
        source_record_id=item.source_record_id,
        source_report_id=source_report_id,
        tool_call_id=tool_call.id if tool_call is not None else None,
        context_hash=item.context_hash,
        created_at=item.created_at,
        confidence=item.confidence,
        summary=item.summary,
        data=compress_data(item.evidence_type, data_json),
        warnings=warnings,
        tags=build_tags(item, data_json),
        source_ref=EvidenceSourceRef(
            evidence_item_id=item.id,
            tool_call_id=tool_call.id if tool_call is not None else None,
            source_type=normalize_source(item.source_type),
            source_table=item.source_table,
            source_report_id=source_report_id,
        ),
    )


def find_tool_call(item: MasEvidenceItem, tool_calls: list[MasToolCall]) -> MasToolCall | None:
    """Find related tool call.
    Args:
        item (MasEvidenceItem): Atomic evidence item.
        tool_calls (list[MasToolCall]): MAS tool calls."""
    tool_name = read_tool_name(item.data_json or {})
    if tool_name is None:
        return None
    matches = [tool_call for tool_call in tool_calls if tool_call.tool_name == tool_name]
    if not matches:
        return None
    return matches[-1]


def read_tool_name(data_json: dict[str, Any]) -> str | None:
    """Read tool name.
    Args:
        data_json (dict[str, Any]): Evidence payload."""
    value = data_json.get('tool_name')
    if isinstance(value, str):
        return value
    return None


def group_evidence(items: list[EvidencePackItem]) -> EvidenceSections:
    """Group evidence items.
    Args:
        items (list[EvidencePackItem]): Evidence pack items."""
    sections = EvidenceSections()
    for item in items:
        section_name = PACK_SECTIONS.get(item.type)
        if section_name is not None:
            getattr(sections, section_name).append(item)
    return sections


def build_missing(run: MasRun, sections: EvidenceSections) -> list[MissingEvidenceItem]:
    """Build missing evidence.
    Args:
        run (MasRun): MAS run record.
        sections (EvidenceSections): Grouped evidence."""
    required_types = REQUIRED_BY_INTENT.get(resolve_intent(run), REQUIRED_BY_INTENT['general_country_summary'])
    missing_items: list[MissingEvidenceItem] = []
    present_types = present_evidence_types(sections)
    for evidence_type in required_types:
        if evidence_type not in present_types:
            missing_items.append(
                MissingEvidenceItem(
                    type=evidence_type,
                    reason=f'No {evidence_type} evidence is available for the resolved context.',
                    severity='high' if evidence_type in CRITICAL_TYPES else 'medium',
                )
            )
    return missing_items


def resolve_intent(run: MasRun) -> str:
    """Resolve evidence intent.
    Args:
        run (MasRun): MAS run record."""
    if run.strategy_mode == 'market_entry':
        return 'market_entry'
    if run.strategy_mode == 'existing_presence':
        return 'existing_presence'
    if run.resolved_intent == 'general_country_summary':
        return 'general_country_summary'
    return 'general_country_summary'


def present_evidence_types(sections: EvidenceSections) -> set[str]:
    """Read present evidence types.
    Args:
        sections (EvidenceSections): Grouped evidence."""
    present_types: set[str] = set()
    section_payload = sections.model_dump()
    for items in section_payload.values():
        for item in items:
            present_types.add(item['type'])
    return present_types


def calculate_quality(items: list[EvidencePackItem], missing: list[MissingEvidenceItem]) -> EvidenceQuality:
    """Calculate evidence quality.
    Args:
        items (list[EvidencePackItem]): Evidence pack items.
        missing (list[MissingEvidenceItem]): Missing evidence items."""
    critical_gaps = [item for item in missing if item.severity == 'high']
    completeness = 'complete'
    if not items:
        completeness = 'insufficient'
    elif missing:
        completeness = 'partial'
    confidence = calculate_confidence(items, critical_gaps)
    return EvidenceQuality(overall_confidence=confidence, completeness=completeness, critical_gaps=critical_gaps)


def calculate_confidence(items: list[EvidencePackItem], critical_gaps: list[MissingEvidenceItem]) -> str:
    """Calculate overall confidence.
    Args:
        items (list[EvidencePackItem]): Evidence pack items.
        critical_gaps (list[MissingEvidenceItem]): Critical gaps."""
    if not items:
        return 'unknown'
    if critical_gaps:
        return 'low'
    values = [item.confidence for item in items]
    if values and all(value == 'high' for value in values):
        return 'high'
    if any(value in {'high', 'medium'} for value in values):
        return 'medium'
    return 'low'


def build_context(run: MasRun) -> EvidenceResolvedContext:
    """Build resolved context.
    Args:
        run (MasRun): MAS run record."""
    context_json = run.resolved_context_json or {}
    return EvidenceResolvedContext(
        project_id=run.project_id,
        country=context_json.get('country'),
        company=context_json.get('company'),
        period={'from': run.date_from, 'to': run.date_to},
        strategy_mode=run.strategy_mode,
        budget_amount=run.budget_amount,
        currency=run.currency,
        context_hash=context_json.get('context_hash'),
    )


def build_failed(tool_calls: list[MasToolCall]) -> list[FailedEvidenceItem]:
    """Build failed evidence.
    Args:
        tool_calls (list[MasToolCall]): MAS tool calls."""
    failed_items: list[FailedEvidenceItem] = []
    for tool_call in tool_calls:
        if tool_call.status == 'failed':
            failed_items.append(
                FailedEvidenceItem(
                    tool_name=tool_call.tool_name,
                    evidence_type=read_output_type(tool_call.output_json or {}),
                    error=tool_call.error_message or read_output_error(tool_call.output_json or {}),
                    severity='medium',
                )
            )
    return failed_items


def read_output_type(output_json: dict[str, Any]) -> str:
    """Read output evidence type.
    Args:
        output_json (dict[str, Any]): Tool output."""
    value = output_json.get('evidence_type')
    if isinstance(value, str):
        return value
    return 'unknown'


def read_output_error(output_json: dict[str, Any]) -> str:
    """Read output error.
    Args:
        output_json (dict[str, Any]): Tool output."""
    errors = output_json.get('errors')
    if isinstance(errors, list) and errors:
        return str(errors[0])
    return 'Tool failed without detailed error.'


def to_llm_context(pack: EvidencePack) -> EvidenceLLMContext:
    """Build LLM context.
    Args:
        pack (EvidencePack): Evidence pack."""
    key_evidence: list[LLMContextItem] = []
    for item in flatten_sections(pack.evidence):
        key_evidence.append(
            LLMContextItem(
                type=item.type,
                summary=item.summary,
                confidence=item.confidence,
                source_ref=f'evidence:{item.type}:{item.id}',
                key_data=compact_key_data(item),
            )
        )
    return EvidenceLLMContext(
        context=pack.resolved_context,
        key_evidence=key_evidence,
        warnings=pack.warnings,
        missing_evidence=pack.missing_evidence,
        evidence_quality=pack.evidence_quality,
    )


def flatten_sections(sections: EvidenceSections) -> list[EvidencePackItem]:
    """Flatten evidence sections.
    Args:
        sections (EvidenceSections): Grouped evidence."""
    items: list[EvidencePackItem] = []
    for section_items in sections.model_dump().values():
        for section_item in section_items:
            items.append(EvidencePackItem(**section_item))
    return items


def validate_pack(pack: EvidencePack) -> EvidencePack:
    """Validate evidence pack.
    Args:
        pack (EvidencePack): Evidence pack."""
    if not pack.mas_run_id:
        raise ValueError('Evidence pack must have mas_run_id.')
    if pack.resolved_context.context_hash is None:
        pack.warnings.append('Evidence pack has no context_hash.')
    if not flatten_sections(pack.evidence):
        pack.warnings.append('Evidence pack has no evidence items.')
    return pack


def save_pack(
    session: Session,
    run: MasRun,
    pack: EvidencePack,
    llm_context: EvidenceLLMContext,
) -> MasEvidencePack:
    """Save evidence pack.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        pack (EvidencePack): Evidence pack.
        llm_context (EvidenceLLMContext): LLM context."""
    record = MasEvidencePack(
        id=pack.pack_id,
        mas_run_id=run.id,
        context_hash=pack.resolved_context.context_hash,
        pack_json=pack.model_dump(mode='json'),
        llm_context_json=llm_context.model_dump(mode='json'),
        quality_json=pack.evidence_quality.model_dump(mode='json'),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def collect_warnings(items: list[EvidencePackItem]) -> list[str]:
    """Collect evidence warnings.
    Args:
        items (list[EvidencePackItem]): Evidence pack items."""
    warnings: list[str] = []
    for item in items:
        warnings.extend(item.warnings)
    return list(dict.fromkeys(warnings))


def read_warnings(data_json: dict[str, Any]) -> list[str]:
    """Read warnings from evidence data.
    Args:
        data_json (dict[str, Any]): Evidence payload."""
    warnings = data_json.get('warnings')
    if isinstance(warnings, list):
        return [str(item) for item in warnings]
    return []


def read_report_id(item: MasEvidenceItem) -> str | None:
    """Read report identifier.
    Args:
        item (MasEvidenceItem): Atomic evidence item."""
    if item.source_type == 'budget_strategy':
        return item.source_record_id
    data = item.data_json or {}
    report_id = data.get('budget_strategy_report_id')
    if report_id is not None:
        return str(report_id)
    return None


def normalize_source(source_type: str) -> str:
    """Normalize source type.
    Args:
        source_type (str): Source type."""
    if source_type == 'budget_strategy':
        return 'budget_strategy_report'
    if source_type == 'report':
        return 'budget_strategy_report'
    return source_type


def build_tags(item: MasEvidenceItem, data_json: dict[str, Any]) -> list[str]:
    """Build evidence tags.
    Args:
        item (MasEvidenceItem): Atomic evidence item.
        data_json (dict[str, Any]): Evidence payload."""
    tags = [item.evidence_type]
    context = data_json.get('context')
    if isinstance(context, dict):
        for key in ('strategy_mode', 'country_name', 'country_code', 'company_name'):
            value = context.get(key)
            if value:
                tags.append(str(value).lower())
    return list(dict.fromkeys(tags))


def compress_data(evidence_type: str, data_json: dict[str, Any]) -> dict[str, Any]:
    """Compress evidence data.
    Args:
        evidence_type (str): Evidence type.
        data_json (dict[str, Any]): Evidence payload."""
    data = data_json.get('data') if isinstance(data_json.get('data'), dict) else data_json
    if not isinstance(data, dict):
        return {'value': data}
    if evidence_type == 'channel':
        return pick_keys(data, ['tool_scope', 'overall_scope', 'company_scope', 'competitor_scope'])
    if evidence_type == 'device':
        return pick_keys(data, ['tool_scope', 'overall_scope', 'company_scope', 'competitor_scope'])
    if evidence_type == 'budget_strategy':
        return pick_keys(
            data,
            ['id', 'budget_strategy_report_id', 'recommended_approach', 'allocation', 'risks', 'dependency_status'],
        )
    if evidence_type == 'opportunity_score':
        return pick_keys(data, ['dependency_status', 'scores'])
    if evidence_type == 'signal':
        return pick_keys(data, ['dependency_status', 'signals'])
    if evidence_type in {'methodology', 'historical_report', 'insight'}:
        return pick_keys(data, ['query', 'results'])
    return data


def pick_keys(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """Pick keys from dictionary.
    Args:
        data (dict[str, Any]): Source data.
        keys (list[str]): Keys to keep."""
    return {key: data[key] for key in keys if key in data}


def compact_key_data(item: EvidencePackItem) -> dict[str, Any]:
    """Build compact key data.
    Args:
        item (EvidencePackItem): Evidence item."""
    data = item.data
    if item.type in {'channel', 'device'}:
        return {'tool_scope': data.get('tool_scope')}
    if item.type == 'budget_strategy':
        return pick_keys(data, ['budget_strategy_report_id', 'recommended_approach', 'allocation'])
    if item.type == 'opportunity_score':
        return pick_keys(data, ['dependency_status', 'scores'])
    if item.type in {'methodology', 'historical_report', 'insight'}:
        results = data.get('results', [])
        return {'results_count': len(results) if isinstance(results, list) else 0}
    return data
