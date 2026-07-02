from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.history.schemas import RecommendationStatusUpdate
from app.models.tables import Insight, KnowledgeDocument, MasRun, Recommendation, ReportSnapshot

REPORT_TYPES = {
    'mas_analysis',
    'country_report',
    'budget_strategy',
    'market_entry_report',
    'existing_presence_report',
    'comparison_report',
}
RECOMMENDATION_STATUSES = {
    'proposed',
    'accepted',
    'rejected',
    'in_progress',
    'completed',
    'archived',
    'superseded',
}


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def build_history(session: Session, run: MasRun) -> ReportSnapshot | None:
    """Build history records.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record."""
    if run.status not in {'completed', 'partial'} or not run.synthesis_output_json:
        return None
    snapshot = create_snapshot(session, run)
    create_insights(session, run, snapshot)
    create_recommendations(session, run, snapshot)
    create_documents(session, run, snapshot)
    return snapshot


def create_snapshot(session: Session, run: MasRun) -> ReportSnapshot:
    """Create report snapshot.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record."""
    existing = session.scalar(select(ReportSnapshot).where(ReportSnapshot.mas_run_id == run.id).limit(1))
    if existing is not None:
        return existing
    supersede_snapshots(session, run)
    report_type = report_type_for(run)
    record = ReportSnapshot(
        project_id=run.project_id,
        report_type=report_type,
        source_type='mas_run',
        source_record_id=str(run.id),
        mas_run_id=run.id,
        context_hash=read_context_hash(run),
        strategy_mode=run.strategy_mode,
        country_id=run.country_id,
        company_id=run.company_id,
        company_domain=read_context_text(run, 'company_domain'),
        period_from=run.date_from,
        period_to=run.date_to,
        budget_amount=run.budget_amount,
        currency=run.currency,
        calculation_version=read_context_text(run, 'calculation_version') or 'v1',
        scoring_version=read_score_version(run),
        prompt_version_id=run.prompt_version_id,
        llm_provider=run.default_llm_provider,
        llm_model=run.default_llm_model,
        title=snapshot_title(run),
        summary=run.final_summary or run.user_query,
        report_json=snapshot_payload(run),
        markdown_snapshot=run.final_answer,
        status='active',
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def supersede_snapshots(session: Session, run: MasRun) -> list[ReportSnapshot]:
    """Supersede previous snapshots.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record."""
    context_hash = read_context_hash(run)
    if context_hash is None:
        return []
    records = list(
        session.scalars(
            select(ReportSnapshot).where(
                ReportSnapshot.project_id == run.project_id,
                ReportSnapshot.context_hash == context_hash,
                ReportSnapshot.report_type == report_type_for(run),
                ReportSnapshot.status == 'active',
            )
        ).all()
    )
    for record in records:
        record.status = 'superseded'
    if records:
        session.commit()
    return records


def create_insights(session: Session, run: MasRun, snapshot: ReportSnapshot) -> list[Insight]:
    """Create insights.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        snapshot (ReportSnapshot): Report snapshot."""
    if has_insights(session, run.id):
        return []
    output = run.synthesis_output_json or {}
    records: list[Insight] = []
    for finding in read_list(output, 'key_findings'):
        records.append(build_insight(run, snapshot, finding, 'market_opportunity', 'finding'))
    for risk in read_list(output, 'risks'):
        records.append(build_insight(run, snapshot, risk, 'market_risk', 'risk'))
    for record in records:
        session.add(record)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def create_recommendations(session: Session, run: MasRun, snapshot: ReportSnapshot) -> list[Recommendation]:
    """Create recommendations.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        snapshot (ReportSnapshot): Report snapshot."""
    if has_recommendations(session, run.id):
        return []
    records: list[Recommendation] = []
    for action in read_list(run.synthesis_output_json or {}, 'recommended_next_actions'):
        records.append(build_recommendation(run, snapshot, action))
    for record in records:
        session.add(record)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def create_documents(session: Session, run: MasRun, snapshot: ReportSnapshot) -> list[KnowledgeDocument]:
    """Create knowledge documents.
    Args:
        session (Session): Active database session.
        run (MasRun): MAS run record.
        snapshot (ReportSnapshot): Report snapshot."""
    records = [
        create_document(
            session,
            run.project_id,
            'mas_run_summary',
            'mas_run',
            str(run.id),
            snapshot.title,
            snapshot.summary,
            {'report_snapshot_id': str(snapshot.id), 'strategy_mode': run.strategy_mode},
        )
    ]
    insights = list(
        session.scalars(
            select(Insight).where(
                Insight.project_id == run.project_id,
                Insight.mas_run_id == run.id,
            )
        ).all()
    )
    for insight in insights:
        records.append(
            create_document(
                session,
                run.project_id,
                'insight',
                'insight',
                str(insight.id),
                insight.title,
                insight.summary,
                {'report_snapshot_id': str(snapshot.id), 'insight_type': insight.insight_type},
            )
        )
    return [record for record in records if record is not None]


def create_document(
    session: Session,
    project_id: UUID,
    document_type: str,
    source_type: str,
    source_record_id: str,
    title: str,
    content: str,
    metadata: dict[str, Any],
) -> KnowledgeDocument | None:
    """Create knowledge document.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        document_type (str): Knowledge document type.
        source_type (str): Source type.
        source_record_id (str): Source record identifier.
        title (str): Document title.
        content (str): Document content.
        metadata (dict[str, Any]): Document metadata."""
    existing = session.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.project_id == project_id,
            KnowledgeDocument.source_type == source_type,
            KnowledgeDocument.source_record_id == source_record_id,
        )
    )
    if existing is not None:
        return existing
    record = KnowledgeDocument(
        project_id=project_id,
        document_type=document_type,
        source_type=source_type,
        source_record_id=source_record_id,
        title=title,
        content=content,
        metadata_json=metadata,
        status='ready',
        version='v1',
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def build_insight(
    run: MasRun,
    snapshot: ReportSnapshot,
    payload: dict[str, Any],
    insight_type: str,
    category: str,
) -> Insight:
    """Build insight.
    Args:
        run (MasRun): MAS run record.
        snapshot (ReportSnapshot): Report snapshot.
        payload (dict[str, Any]): Synthesis payload.
        insight_type (str): Insight type.
        category (str): Insight category."""
    title = str(payload.get('finding') or payload.get('risk') or category).strip()
    summary = str(payload.get('finding') or payload.get('risk') or payload.get('mitigation') or title).strip()
    return Insight(
        project_id=run.project_id,
        source_type='mas_synthesis',
        source_record_id=str(run.id),
        mas_run_id=run.id,
        report_snapshot_id=snapshot.id,
        evidence_item_id=resolve_evidence(run, payload),
        insight_type=insight_type,
        category=category,
        severity=str(payload.get('severity')) if payload.get('severity') else None,
        country_id=run.country_id,
        company_id=run.company_id,
        strategy_mode=run.strategy_mode,
        period_from=run.date_from,
        period_to=run.date_to,
        title=title[:300],
        summary=summary,
        details_json=payload,
        confidence=str(payload.get('confidence') or snapshot.report_json.get('confidence') or 'medium'),
        status='active',
        tags=build_tags(run, [insight_type, category]),
    )


def build_recommendation(run: MasRun, snapshot: ReportSnapshot, payload: dict[str, Any]) -> Recommendation:
    """Build recommendation.
    Args:
        run (MasRun): MAS run record.
        snapshot (ReportSnapshot): Report snapshot.
        payload (dict[str, Any]): Synthesis action payload."""
    action = str(payload.get('action') or 'Review MAS recommendation.').strip()
    priority = str(payload.get('priority') or 'medium')
    return Recommendation(
        project_id=run.project_id,
        source_type='mas_synthesis',
        source_record_id=str(run.id),
        mas_run_id=run.id,
        report_snapshot_id=snapshot.id,
        insight_id=None,
        recommendation_type=recommendation_type(run, action),
        strategy_mode=run.strategy_mode,
        country_id=run.country_id,
        company_id=run.company_id,
        period_from=run.date_from,
        period_to=run.date_to,
        title=action[:300],
        description=action,
        action=action,
        priority=priority,
        channel=extract_channel(action),
        budget_share=None,
        budget_amount=run.budget_amount,
        currency=run.currency,
        confidence=str(snapshot.report_json.get('confidence') or 'medium'),
        status='proposed',
        linked_mas_run_id=run.id,
        linked_evidence_item_ids=[str(item) for item in payload.get('evidence_refs', []) if item],
    )


def list_reports(
    session: Session,
    project_id: UUID,
    filters: dict[str, Any],
    limit: int,
    offset: int,
) -> tuple[list[ReportSnapshot], int]:
    """List report snapshots.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Filter values.
        limit (int): Result limit.
        offset (int): Result offset."""
    where = report_filters(project_id, filters)
    query = select(ReportSnapshot).where(*where).order_by(ReportSnapshot.created_at.desc()).offset(offset).limit(limit)
    total = int(session.scalar(select(func.count()).select_from(ReportSnapshot).where(*where)) or 0)
    return list(session.scalars(query).all()), total


def list_insights(
    session: Session,
    project_id: UUID,
    filters: dict[str, Any],
    limit: int,
    offset: int,
) -> tuple[list[Insight], int]:
    """List insights.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Filter values.
        limit (int): Result limit.
        offset (int): Result offset."""
    where = insight_filters(project_id, filters)
    query = select(Insight).where(*where).order_by(Insight.created_at.desc()).offset(offset).limit(limit)
    total = int(session.scalar(select(func.count()).select_from(Insight).where(*where)) or 0)
    return list(session.scalars(query).all()), total


def list_recommendations(
    session: Session,
    project_id: UUID,
    filters: dict[str, Any],
    limit: int,
    offset: int,
) -> tuple[list[Recommendation], int]:
    """List recommendations.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Filter values.
        limit (int): Result limit.
        offset (int): Result offset."""
    where = recommendation_filters(project_id, filters)
    query = select(Recommendation).where(*where).order_by(Recommendation.created_at.desc()).offset(offset).limit(limit)
    total = int(session.scalar(select(func.count()).select_from(Recommendation).where(*where)) or 0)
    return list(session.scalars(query).all()), total


def read_report(session: Session, project_id: UUID, record_id: UUID) -> ReportSnapshot | None:
    """Read report snapshot.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        record_id (UUID): Report snapshot identifier."""
    return session.scalar(
        select(ReportSnapshot).where(
            ReportSnapshot.project_id == project_id,
            ReportSnapshot.id == record_id,
        )
    )


def read_insight(session: Session, project_id: UUID, record_id: UUID) -> Insight | None:
    """Read insight.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        record_id (UUID): Insight identifier."""
    return session.scalar(select(Insight).where(Insight.project_id == project_id, Insight.id == record_id))


def read_recommendation(session: Session, project_id: UUID, record_id: UUID) -> Recommendation | None:
    """Read recommendation.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        record_id (UUID): Recommendation identifier."""
    return session.scalar(
        select(Recommendation).where(
            Recommendation.project_id == project_id,
            Recommendation.id == record_id,
        )
    )


def update_recommendation(
    session: Session,
    record: Recommendation,
    request: RecommendationStatusUpdate,
) -> Recommendation:
    """Update recommendation status.
    Args:
        session (Session): Active database session.
        record (Recommendation): Recommendation record.
        request (RecommendationStatusUpdate): Status update payload."""
    if request.status not in RECOMMENDATION_STATUSES:
        raise ValueError('Unsupported recommendation status.')
    record.status = request.status
    record.user_decision = request.user_decision
    record.user_decision_reason = request.user_decision_reason
    record.updated_at = current_time()
    session.commit()
    session.refresh(record)
    return record


def report_filters(project_id: UUID, filters: dict[str, Any]) -> list[object]:
    """Build report filters.
    Args:
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Filter values."""
    where: list[object] = [ReportSnapshot.project_id == project_id]
    add_common_report_filters(where, filters)
    if filters.get('report_type'):
        where.append(ReportSnapshot.report_type == filters['report_type'])
    if filters.get('mas_run_id'):
        where.append(ReportSnapshot.mas_run_id == filters['mas_run_id'])
    if filters.get('country_id'):
        where.append(ReportSnapshot.country_id == filters['country_id'])
    if filters.get('company_id'):
        where.append(ReportSnapshot.company_id == filters['company_id'])
    if filters.get('status'):
        where.append(ReportSnapshot.status == filters['status'])
    if filters.get('search'):
        pattern = f"%{filters['search']}%"
        where.append(or_(ReportSnapshot.title.ilike(pattern), ReportSnapshot.summary.ilike(pattern)))
    return where


def insight_filters(project_id: UUID, filters: dict[str, Any]) -> list[object]:
    """Build insight filters.
    Args:
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Filter values."""
    where: list[object] = [Insight.project_id == project_id]
    add_common_entity_filters(where, Insight, filters)
    if filters.get('insight_type'):
        where.append(Insight.insight_type == filters['insight_type'])
    if filters.get('mas_run_id'):
        where.append(Insight.mas_run_id == filters['mas_run_id'])
    if filters.get('country_id'):
        where.append(Insight.country_id == filters['country_id'])
    if filters.get('company_id'):
        where.append(Insight.company_id == filters['company_id'])
    if filters.get('severity'):
        where.append(Insight.severity == filters['severity'])
    if filters.get('confidence'):
        where.append(Insight.confidence == filters['confidence'])
    if filters.get('status'):
        where.append(Insight.status == filters['status'])
    if filters.get('search'):
        pattern = f"%{filters['search']}%"
        where.append(or_(Insight.title.ilike(pattern), Insight.summary.ilike(pattern)))
    return where


def recommendation_filters(project_id: UUID, filters: dict[str, Any]) -> list[object]:
    """Build recommendation filters.
    Args:
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Filter values."""
    where: list[object] = [Recommendation.project_id == project_id]
    add_common_entity_filters(where, Recommendation, filters)
    if filters.get('recommendation_type'):
        where.append(Recommendation.recommendation_type == filters['recommendation_type'])
    if filters.get('mas_run_id'):
        where.append(Recommendation.mas_run_id == filters['mas_run_id'])
    if filters.get('country_id'):
        where.append(Recommendation.country_id == filters['country_id'])
    if filters.get('company_id'):
        where.append(Recommendation.company_id == filters['company_id'])
    if filters.get('confidence'):
        where.append(Recommendation.confidence == filters['confidence'])
    if filters.get('status'):
        where.append(Recommendation.status == filters['status'])
    if filters.get('search'):
        pattern = f"%{filters['search']}%"
        where.append(or_(Recommendation.title.ilike(pattern), Recommendation.description.ilike(pattern)))
    return where


def add_common_report_filters(where: list[object], filters: dict[str, Any]) -> list[object]:
    """Add common report filters.
    Args:
        where (list[object]): Existing filters.
        filters (dict[str, Any]): Filter values."""
    if filters.get('strategy_mode'):
        where.append(ReportSnapshot.strategy_mode == filters['strategy_mode'])
    if filters.get('period_from'):
        where.append(ReportSnapshot.period_from >= filters['period_from'])
    if filters.get('period_to'):
        where.append(ReportSnapshot.period_to <= filters['period_to'])
    if filters.get('created_from'):
        where.append(ReportSnapshot.created_at >= filters['created_from'])
    if filters.get('created_to'):
        where.append(ReportSnapshot.created_at <= filters['created_to'])
    return where


def add_common_entity_filters(where: list[object], model: object, filters: dict[str, Any]) -> list[object]:
    """Add common entity filters.
    Args:
        where (list[object]): Existing filters.
        model (object): SQLAlchemy model.
        filters (dict[str, Any]): Filter values."""
    if filters.get('strategy_mode'):
        where.append(model.strategy_mode == filters['strategy_mode'])
    if filters.get('period_from'):
        where.append(model.period_from >= filters['period_from'])
    if filters.get('period_to'):
        where.append(model.period_to <= filters['period_to'])
    if filters.get('created_from'):
        where.append(model.created_at >= filters['created_from'])
    if filters.get('created_to'):
        where.append(model.created_at <= filters['created_to'])
    return where


def has_insights(session: Session, run_id: UUID) -> bool:
    """Check existing insights.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    return session.scalar(select(Insight.id).where(Insight.mas_run_id == run_id).limit(1)) is not None


def has_recommendations(session: Session, run_id: UUID) -> bool:
    """Check existing recommendations.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier."""
    return session.scalar(select(Recommendation.id).where(Recommendation.mas_run_id == run_id).limit(1)) is not None


def report_type_for(run: MasRun) -> str:
    """Build report type.
    Args:
        run (MasRun): MAS run record."""
    if run.strategy_mode == 'market_entry':
        return 'market_entry_report'
    if run.strategy_mode == 'existing_presence':
        return 'existing_presence_report'
    return 'mas_analysis'


def snapshot_title(run: MasRun) -> str:
    """Build snapshot title.
    Args:
        run (MasRun): MAS run record."""
    country = read_context_text(run, 'country') or 'selected market'
    company = read_context_text(run, 'company') or 'selected company'
    return f'MAS {run.strategy_mode or "analysis"}: {company} in {country}'


def snapshot_payload(run: MasRun) -> dict[str, Any]:
    """Build snapshot payload.
    Args:
        run (MasRun): MAS run record."""
    return {
        'user_query': run.user_query,
        'resolved_intent': run.resolved_intent,
        'resolved_context': run.resolved_context_json,
        'planner_output': run.planner_output_json,
        'synthesis_output': run.synthesis_output_json,
        'confidence': (run.synthesis_output_json or {}).get('confidence'),
        'metrics': run.metrics_json,
    }


def read_context_text(run: MasRun, key: str) -> str | None:
    """Read context text.
    Args:
        run (MasRun): MAS run record.
        key (str): Context key."""
    value = (run.resolved_context_json or {}).get(key)
    if value is None:
        return None
    return str(value)


def read_context_hash(run: MasRun) -> str | None:
    """Read context hash.
    Args:
        run (MasRun): MAS run record."""
    value = read_context_text(run, 'context_hash')
    if value is not None:
        return value
    metrics = run.metrics_json or {}
    metric_value = metrics.get('context_hash')
    if metric_value is not None:
        return str(metric_value)
    return None


def read_score_version(run: MasRun) -> str | None:
    """Read scoring version.
    Args:
        run (MasRun): MAS run record."""
    output = run.synthesis_output_json or {}
    value = output.get('scoring_version')
    if value is None:
        return None
    return str(value)


def read_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Read list payload.
    Args:
        data (dict[str, Any]): Source payload.
        key (str): Source key."""
    value = data.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def resolve_evidence(run: MasRun, payload: dict[str, Any]) -> UUID | None:
    """Resolve linked evidence.
    Args:
        run (MasRun): MAS run record.
        payload (dict[str, Any]): Source payload."""
    refs = payload.get('evidence_refs')
    if not isinstance(refs, list) or not refs:
        return None
    first_ref = str(refs[0])
    parts = first_ref.split(':')
    if len(parts) < 3:
        return None
    try:
        return UUID(parts[-1])
    except ValueError:
        return None


def build_tags(run: MasRun, tags: list[str]) -> list[str]:
    """Build history tags.
    Args:
        run (MasRun): MAS run record.
        tags (list[str]): Source tags."""
    values = [tag for tag in tags if tag]
    if run.strategy_mode:
        values.append(run.strategy_mode)
    country = read_context_text(run, 'country')
    company = read_context_text(run, 'company')
    if country:
        values.append(country.lower())
    if company:
        values.append(company.lower())
    return list(dict.fromkeys(values))


def recommendation_type(run: MasRun, action: str) -> str:
    """Build recommendation type.
    Args:
        run (MasRun): MAS run record.
        action (str): Recommended action."""
    text = action.lower()
    if run.strategy_mode == 'market_entry':
        return 'market_entry'
    if 'budget' in text or 'allocation' in text:
        return 'budget_allocation'
    if 'monitor' in text:
        return 'risk_monitoring'
    if 'scale' in text:
        return 'channel_scale'
    if 'test' in text:
        return 'channel_test'
    return 'quality_improvement'


def extract_channel(action: str) -> str | None:
    """Extract channel from action.
    Args:
        action (str): Recommended action."""
    text = action.lower()
    for channel in ('search', 'paid', 'referral', 'social', 'direct'):
        if channel in text:
            return channel
    return None
