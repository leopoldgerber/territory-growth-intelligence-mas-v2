from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.alerts.schemas import AlertDetectRequest, AlertStatusUpdate
from app.analytics.scoring.service import recalculate_scores
from app.analytics.signals.service import recalculate_signals
from app.models.tables import (
    AlertEvent,
    AlertRule,
    AnalyticsRecalculationJob,
    DataFreshnessStatus,
    DataUpdateBatch,
    DerivedSignal,
    FactDeviceTrendsDaily,
    FactJourneySourcesDaily,
    FactTrafficCountriesDaily,
    FactTrafficSourcesDaily,
    IngestionRun,
    Insight,
    OpportunityScore,
)
from app.schemas.analytics import OpportunityScoreRecalculateRequest, RecalculateSignalsRequest

DATASET_MODELS = {
    'traffic_countries': FactTrafficCountriesDaily,
    'traffic_sources': FactTrafficSourcesDaily,
    'journey_sources': FactJourneySourcesDaily,
    'trend_by_devices': FactDeviceTrendsDaily,
}
ALERT_STATUSES = {'new', 'seen', 'acknowledged', 'resolved', 'dismissed', 'archived'}
SEVERITY_ORDER = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
DEFAULT_RULES = [
    ('traffic_spike', 'Traffic spike', 'Traffic increased materially versus baseline.', 'medium'),
    ('traffic_drop', 'Traffic drop', 'Traffic dropped materially versus baseline.', 'medium'),
    ('country_leader_change', 'Country leader change', 'Country traffic leadership changed.', 'high'),
    ('competitor_new_country', 'Competitor new country', 'Competitor appeared in a new active country.', 'medium'),
    ('competitor_left_country', 'Competitor left country', 'Competitor disappeared from an active country.', 'high'),
    ('channel_spike_paid', 'Paid channel spike', 'Paid channel share increased materially.', 'medium'),
    ('channel_spike_referral', 'Referral channel spike', 'Referral channel share increased materially.', 'medium'),
    ('channel_spike_social', 'Social channel spike', 'Social channel share increased materially.', 'medium'),
    ('traffic_quality_drop', 'Traffic quality drop', 'Traffic engagement quality weakened.', 'high'),
    ('market_window', 'Market window', 'Opportunity conditions look favorable.', 'medium'),
    ('opportunity_score_change', 'Opportunity score change', 'Opportunity score reached a meaningful level.', 'medium'),
    ('signal_severity_increase', 'Signal severity increase', 'A persisted signal reached high severity.', 'high'),
    ('budget_strategy_outdated', 'Budget strategy outdated', 'Budget strategy may need refresh.', 'medium'),
]


class AlertCandidate:
    def __init__(
        self,
        alert_type: str,
        severity: str,
        title: str,
        summary: str,
        details: dict[str, Any],
        country_id: int | None = None,
        company_id: int | None = None,
        competitor_id: int | None = None,
        channel: str | None = None,
        related_signal_ids: list[int] | None = None,
        related_score_ids: list[int] | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        context_hash: str | None = None,
    ) -> None:
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.summary = summary
        self.details = details
        self.country_id = country_id
        self.company_id = company_id
        self.competitor_id = competitor_id
        self.channel = channel
        self.related_signal_ids = related_signal_ids or []
        self.related_score_ids = related_score_ids or []
        self.evidence_refs = evidence_refs or []
        self.context_hash = context_hash


class DataUpdateScheduler:
    def run_scheduled_update(
        self,
        session: Session,
        project_id: UUID,
        calculation_version: str = 'v1',
    ) -> dict[str, Any]:
        """Run scheduled update.
        Args:
            session (Session): Active database session.
            project_id (UUID): Project identifier.
            calculation_version (str): Calculation version."""
        period_from, period_to = read_period(session, project_id, None, None)
        request = AlertDetectRequest(date_from=period_from, date_to=period_to, calculation_version=calculation_version)
        return run_manual_update(session, project_id, request)

    def run_manual_update(
        self,
        session: Session,
        project_id: UUID,
        request: AlertDetectRequest,
    ) -> dict[str, Any]:
        """Run manual update.
        Args:
            session (Session): Active database session.
            project_id (UUID): Project identifier.
            request (AlertDetectRequest): Alert detection request."""
        return run_manual_update(session, project_id, request)

    def get_update_status(self, session: Session, project_id: UUID) -> dict[str, Any]:
        """Get update status.
        Args:
            session (Session): Active database session.
            project_id (UUID): Project identifier."""
        return read_update_status(session, project_id)


class AlertDetectionService:
    def detect_period(
        self,
        session: Session,
        project_id: UUID,
        period_from: date | None,
        period_to: date | None,
        calculation_version: str,
    ) -> dict[str, Any]:
        """Detect period alerts.
        Args:
            session (Session): Active database session.
            project_id (UUID): Project identifier.
            period_from (date | None): Period start.
            period_to (date | None): Period end.
            calculation_version (str): Calculation version."""
        return detect_period(session, project_id, period_from, period_to, calculation_version)

    def detect_batch(
        self,
        session: Session,
        batch: DataUpdateBatch,
        calculation_version: str,
    ) -> dict[str, Any]:
        """Detect batch alerts.
        Args:
            session (Session): Active database session.
            batch (DataUpdateBatch): Data update batch.
            calculation_version (str): Calculation version."""
        return detect_period(session, batch.project_id, batch.period_from, batch.period_to, calculation_version)


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def sync_ingestion(session: Session, ingestion_run: IngestionRun) -> DataUpdateBatch | None:
    """Sync ingestion update.
    Args:
        session (Session): Active database session.
        ingestion_run (IngestionRun): Ingestion run model."""
    if ingestion_run.file_type not in DATASET_MODELS:
        return None
    batch = session.get(DataUpdateBatch, ingestion_run.id)
    if batch is None:
        batch = DataUpdateBatch(
            id=ingestion_run.id,
            project_id=ingestion_run.project_id,
            source_type=ingestion_run.file_type,
        )
        session.add(batch)
    batch.source_file = ingestion_run.file_name
    batch.period_from = ingestion_run.period_start
    batch.period_to = ingestion_run.period_end
    batch.status = map_batch_status(ingestion_run.status)
    batch.rows_loaded = int(ingestion_run.inserted_row_count or 0)
    batch.rows_failed = int(ingestion_run.failed_row_count or ingestion_run.invalid_row_count or 0)
    batch.validation_status = ingestion_run.validation_status
    batch.started_at = ingestion_run.started_at
    batch.completed_at = ingestion_run.finished_at
    batch.error_message = ingestion_run.error_message
    batch.metadata_json = {
        'ingestion_run_id': str(ingestion_run.id),
        'checksum': ingestion_run.checksum,
        'duplicates_skipped': int(ingestion_run.skipped_duplicate_count or 0),
        'valid_rows': int(ingestion_run.valid_row_count or 0),
    }
    session.flush()
    update_freshness(session, batch)
    if batch.status in {'completed', 'partial'} and batch.rows_loaded > 0:
        request = AlertDetectRequest(date_from=batch.period_from, date_to=batch.period_to, run_recalculation=True)
        run_pipeline(session, batch.project_id, batch, request)
    return batch


def run_manual_update(session: Session, project_id: UUID, request: AlertDetectRequest) -> dict[str, Any]:
    """Run manual alert update.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (AlertDetectRequest): Alert detection request."""
    period_from, period_to = read_period(session, project_id, request.date_from, request.date_to)
    batch = DataUpdateBatch(
        project_id=project_id,
        source_type='manual_trigger',
        source_file=None,
        period_from=period_from,
        period_to=period_to,
        status='running',
        rows_loaded=0,
        rows_failed=0,
        validation_status='not_applicable',
        started_at=current_time(),
        metadata_json={'trigger': 'manual'},
    )
    session.add(batch)
    session.commit()
    try:
        result = run_pipeline(session, project_id, batch, request)
        batch.status = 'completed'
        batch.completed_at = current_time()
        session.commit()
        result['data_update_batch'] = batch
        return result
    except Exception as error:
        session.rollback()
        batch.status = 'failed'
        batch.error_message = str(error)
        batch.completed_at = current_time()
        session.add(batch)
        session.commit()
        raise


def run_pipeline(
    session: Session,
    project_id: UUID,
    batch: DataUpdateBatch | None,
    request: AlertDetectRequest,
) -> dict[str, Any]:
    """Run recalculation pipeline.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        batch (DataUpdateBatch | None): Optional data update batch.
        request (AlertDetectRequest): Alert detection request."""
    period_from, period_to = read_period(session, project_id, request.date_from, request.date_to)
    jobs: list[AnalyticsRecalculationJob] = []
    if request.run_recalculation:
        for job_type in ('country_metrics', 'competitor_metrics', 'channel_metrics', 'device_metrics'):
            jobs.append(record_metric_job(session, project_id, batch, job_type, period_from, period_to))
        jobs.append(run_signals_job(session, project_id, batch, period_from, period_to, request.calculation_version))
        jobs.append(run_scoring_job(session, project_id, batch, period_from, period_to, request.calculation_version))
    detection_job = create_job(
        session,
        project_id,
        batch,
        'alert_detection',
        period_from,
        period_to,
        request.calculation_version,
    )
    try:
        result = detect_period(session, project_id, period_from, period_to, request.calculation_version)
        finish_job(
            session,
            detection_job,
            'completed',
            {'created': result['created'], 'updated': result['updated']},
            None,
        )
    except Exception as error:
        finish_job(session, detection_job, 'failed', {}, str(error))
        raise
    jobs.append(detection_job)
    return {'jobs': jobs, 'alert_result': result}


def detect_period(
    session: Session,
    project_id: UUID,
    period_from: date | None,
    period_to: date | None,
    calculation_version: str,
) -> dict[str, Any]:
    """Detect alerts for period.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        period_from (date | None): Period start.
        period_to (date | None): Period end.
        calculation_version (str): Calculation version."""
    ensure_rules(session, project_id)
    rules = read_rules(session, project_id)
    candidates = [
        *build_signal_alerts(session, project_id, period_from, period_to, calculation_version),
        *build_score_alerts(session, project_id, period_from, period_to, calculation_version),
    ]
    events: list[AlertEvent] = []
    created_count = 0
    updated_count = 0
    for candidate in candidates:
        rule = rules.get(candidate.alert_type)
        if rule is None or not rule.is_enabled:
            continue
        event, created = save_alert(session, project_id, rule, candidate, period_from, period_to)
        link_insight(session, event)
        events.append(event)
        created_count += 1 if created else 0
        updated_count += 0 if created else 1
    session.commit()
    for event in events:
        session.refresh(event)
    return {'created': created_count, 'updated': updated_count, 'events': events}


def build_signal_alerts(
    session: Session,
    project_id: UUID,
    period_from: date | None,
    period_to: date | None,
    calculation_version: str,
) -> list[AlertCandidate]:
    """Build signal alerts.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        period_from (date | None): Period start.
        period_to (date | None): Period end.
        calculation_version (str): Calculation version."""
    filters = [DerivedSignal.project_id == project_id, DerivedSignal.calculation_version == calculation_version]
    if period_from is not None:
        filters.append(DerivedSignal.date_from == period_from)
    if period_to is not None:
        filters.append(DerivedSignal.date_to == period_to)
    records = list(session.scalars(select(DerivedSignal).where(*filters)).all())
    candidates: list[AlertCandidate] = []
    for record in records:
        alert_type = map_signal_type(record)
        if alert_type is None:
            continue
        channel = read_channel(record)
        candidates.append(
            AlertCandidate(
                alert_type=alert_type,
                severity=normalize_severity(record.severity),
                title=alert_title(alert_type, record.message),
                summary=record.message,
                details=record.details or {},
                country_id=record.country_id,
                company_id=record.company_id,
                competitor_id=record.company_id if record.signal_type == 'competitor_expansion' else None,
                channel=channel,
                related_signal_ids=[record.id],
                evidence_refs=[{'source_table': 'derived_signal', 'source_record_id': str(record.id)}],
                context_hash=record.context_hash,
            )
        )
    return candidates


def build_score_alerts(
    session: Session,
    project_id: UUID,
    period_from: date | None,
    period_to: date | None,
    calculation_version: str,
) -> list[AlertCandidate]:
    """Build score alerts.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        period_from (date | None): Period start.
        period_to (date | None): Period end.
        calculation_version (str): Calculation version."""
    filters = [
        OpportunityScore.project_id == project_id,
        OpportunityScore.calculation_version == calculation_version,
        OpportunityScore.score_category.in_(['high', 'very_high']),
    ]
    if period_from is not None:
        filters.append(OpportunityScore.date_from == period_from)
    if period_to is not None:
        filters.append(OpportunityScore.date_to == period_to)
    records = list(session.scalars(select(OpportunityScore).where(*filters)).all())
    candidates: list[AlertCandidate] = []
    for record in records:
        severity = 'high' if record.score_category == 'very_high' else 'medium'
        details = {
            'opportunity_score': float(record.opportunity_score),
            'score_category': record.score_category,
            'rank': record.rank,
            'scope': record.scope,
        }
        candidates.append(
            AlertCandidate(
                alert_type='market_window',
                severity=severity,
                title='Market window detected',
                summary=f'Country {record.country_id} has {record.score_category} opportunity score.',
                details=details,
                country_id=record.country_id,
                related_score_ids=[record.id],
                evidence_refs=[{'source_table': 'opportunity_score', 'source_record_id': str(record.id)}],
                context_hash=record.context_hash,
            )
        )
    return candidates


def save_alert(
    session: Session,
    project_id: UUID,
    rule: AlertRule,
    candidate: AlertCandidate,
    period_from: date | None,
    period_to: date | None,
) -> tuple[AlertEvent, bool]:
    """Save alert event.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        rule (AlertRule): Alert rule.
        candidate (AlertCandidate): Alert candidate.
        period_from (date | None): Period start.
        period_to (date | None): Period end."""
    dedupe_key = build_dedupe(project_id, candidate, period_from, period_to)
    existing = read_existing(session, dedupe_key, rule.cooldown_hours)
    if existing is not None:
        existing.severity = higher_severity(existing.severity, candidate.severity)
        existing.status = 'new' if existing.status in {'seen', 'dismissed'} else existing.status
        existing.summary = candidate.summary
        existing.details_json = candidate.details
        existing.evidence_refs_json = merge_values(existing.evidence_refs_json, candidate.evidence_refs)
        existing.related_signal_ids = merge_values(existing.related_signal_ids, candidate.related_signal_ids)
        existing.related_score_ids = merge_values(existing.related_score_ids, candidate.related_score_ids)
        existing.detected_at = current_time()
        existing.updated_at = current_time()
        session.add(existing)
        session.flush()
        return existing, False
    record = AlertEvent(
        project_id=project_id,
        alert_rule_id=rule.id,
        alert_type=candidate.alert_type,
        severity=higher_severity(rule.severity_default, candidate.severity),
        status='new',
        country_id=candidate.country_id,
        company_id=candidate.company_id,
        competitor_id=candidate.competitor_id,
        channel=candidate.channel,
        period_from=period_from,
        period_to=period_to,
        title=candidate.title,
        summary=candidate.summary,
        details_json=candidate.details,
        evidence_refs_json=candidate.evidence_refs,
        related_signal_ids=candidate.related_signal_ids,
        related_score_ids=candidate.related_score_ids,
        related_insight_ids=[],
        context_hash=candidate.context_hash,
        dedupe_key=dedupe_key,
    )
    session.add(record)
    session.flush()
    return record, True


def link_insight(session: Session, event: AlertEvent) -> AlertEvent:
    """Link alert insight.
    Args:
        session (Session): Active database session.
        event (AlertEvent): Alert event."""
    if SEVERITY_ORDER.get(event.severity, 1) < SEVERITY_ORDER['high']:
        return event
    existing = session.scalar(
        select(Insight).where(
            Insight.project_id == event.project_id,
            Insight.source_type == 'alert_event',
            Insight.source_record_id == str(event.id),
        )
    )
    if existing is not None:
        event.related_insight_ids = [str(existing.id)]
        return event
    insight = Insight(
        project_id=event.project_id,
        source_type='alert_event',
        source_record_id=str(event.id),
        insight_type='proactive_alert',
        category=event.alert_type,
        severity=event.severity,
        country_id=event.country_id,
        company_id=event.company_id,
        strategy_mode=None,
        period_from=event.period_from,
        period_to=event.period_to,
        title=event.title,
        summary=event.summary,
        details_json=event.details_json,
        confidence='medium',
        status='active',
        tags=['alert', event.alert_type, event.severity],
    )
    session.add(insight)
    session.flush()
    event.related_insight_ids = [str(insight.id)]
    return event


def read_update_status(session: Session, project_id: UUID) -> dict[str, Any]:
    """Read update status.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier."""
    freshness = list(
        session.scalars(
            select(DataFreshnessStatus)
            .where(DataFreshnessStatus.project_id == project_id)
            .order_by(DataFreshnessStatus.dataset_type)
        ).all()
    )
    batches = list(
        session.scalars(
            select(DataUpdateBatch)
            .where(DataUpdateBatch.project_id == project_id)
            .order_by(DataUpdateBatch.created_at.desc())
            .limit(10)
        ).all()
    )
    jobs = list(
        session.scalars(
            select(AnalyticsRecalculationJob)
            .where(AnalyticsRecalculationJob.project_id == project_id)
            .order_by(AnalyticsRecalculationJob.started_at.desc())
            .limit(10)
        ).all()
    )
    return {'freshness': freshness, 'latest_batches': batches, 'latest_jobs': jobs}


def list_alerts(
    session: Session,
    project_id: UUID,
    filters: dict[str, Any],
    limit: int,
    offset: int,
) -> tuple[list[AlertEvent], int]:
    """List alert events.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Alert filters.
        limit (int): Result limit.
        offset (int): Result offset."""
    where = alert_filters(project_id, filters)
    query = select(AlertEvent).where(*where).order_by(AlertEvent.detected_at.desc()).offset(offset).limit(limit)
    total = int(session.scalar(select(func.count()).select_from(AlertEvent).where(*where)) or 0)
    return list(session.scalars(query).all()), total


def read_alert(session: Session, project_id: UUID, alert_id: UUID) -> AlertEvent | None:
    """Read alert event.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        alert_id (UUID): Alert event identifier."""
    return session.scalar(select(AlertEvent).where(AlertEvent.project_id == project_id, AlertEvent.id == alert_id))


def update_alert(session: Session, record: AlertEvent, request: AlertStatusUpdate) -> AlertEvent:
    """Update alert status.
    Args:
        session (Session): Active database session.
        record (AlertEvent): Alert event.
        request (AlertStatusUpdate): Status update request."""
    if request.status not in ALERT_STATUSES:
        raise ValueError('Unsupported alert status.')
    record.status = request.status
    record.updated_at = current_time()
    if request.status == 'acknowledged':
        record.acknowledged_at = current_time()
    if request.status == 'resolved':
        record.resolved_at = current_time()
    session.commit()
    session.refresh(record)
    return record


def alert_summary(session: Session, project_id: UUID, filters: dict[str, Any]) -> dict[str, Any]:
    """Build alert summary.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Alert filters."""
    where = alert_filters(project_id, filters)
    records = list(session.scalars(select(AlertEvent).where(*where)).all())
    by_severity = count_values(records, 'severity')
    by_status = count_values(records, 'status')
    by_type = count_values(records, 'alert_type')
    competitor_types = {'competitor_new_country', 'competitor_left_country', 'country_leader_change'}
    return {
        'total': len(records),
        'new_alerts': by_status.get('new', 0),
        'high_severity': sum(1 for record in records if record.severity in {'high', 'critical'}),
        'market_windows': by_type.get('market_window', 0),
        'competitor_movements': sum(by_type.get(alert_type, 0) for alert_type in competitor_types),
        'quality_risks': by_type.get('traffic_quality_drop', 0),
        'by_severity': by_severity,
        'by_status': by_status,
        'by_type': by_type,
    }


def alert_filters(project_id: UUID, filters: dict[str, Any]) -> list[Any]:
    """Build alert filters.
    Args:
        project_id (UUID): Project identifier.
        filters (dict[str, Any]): Alert filters."""
    where: list[Any] = [AlertEvent.project_id == project_id]
    if filters.get('alert_type'):
        where.append(AlertEvent.alert_type == filters['alert_type'])
    if filters.get('severity'):
        where.append(AlertEvent.severity == filters['severity'])
    if filters.get('status'):
        where.append(AlertEvent.status == filters['status'])
    if filters.get('country_id'):
        where.append(AlertEvent.country_id == filters['country_id'])
    if filters.get('company_id'):
        where.append(
            or_(
                AlertEvent.company_id == filters['company_id'],
                AlertEvent.competitor_id == filters['company_id'],
            )
        )
    if filters.get('date_from'):
        where.append(AlertEvent.detected_at >= filters['date_from'])
    if filters.get('date_to'):
        where.append(AlertEvent.detected_at <= filters['date_to'])
    return where


def count_values(records: list[AlertEvent], field_name: str) -> dict[str, int]:
    """Count record values.
    Args:
        records (list[AlertEvent]): Alert events.
        field_name (str): Field name."""
    counts: dict[str, int] = {}
    for record in records:
        value = str(getattr(record, field_name) or 'unknown')
        counts[value] = counts.get(value, 0) + 1
    return counts


def create_job(
    session: Session,
    project_id: UUID,
    batch: DataUpdateBatch | None,
    job_type: str,
    period_from: date | None,
    period_to: date | None,
    calculation_version: str | None,
) -> AnalyticsRecalculationJob:
    """Create recalculation job.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        batch (DataUpdateBatch | None): Optional data update batch.
        job_type (str): Job type.
        period_from (date | None): Period start.
        period_to (date | None): Period end.
        calculation_version (str | None): Calculation version."""
    record = AnalyticsRecalculationJob(
        project_id=project_id,
        data_update_batch_id=batch.id if batch is not None else None,
        job_type=job_type,
        status='running',
        period_from=period_from,
        period_to=period_to,
        calculation_version=calculation_version,
        started_at=current_time(),
        metrics_json={},
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def finish_job(
    session: Session,
    record: AnalyticsRecalculationJob,
    status: str,
    metrics: dict[str, Any],
    error_message: str | None,
) -> AnalyticsRecalculationJob:
    """Finish recalculation job.
    Args:
        session (Session): Active database session.
        record (AnalyticsRecalculationJob): Recalculation job.
        status (str): Final status.
        metrics (dict[str, Any]): Job metrics.
        error_message (str | None): Error message."""
    record.status = status
    record.metrics_json = metrics
    record.error_message = error_message
    record.completed_at = current_time()
    session.commit()
    session.refresh(record)
    return record


def record_metric_job(
    session: Session,
    project_id: UUID,
    batch: DataUpdateBatch | None,
    job_type: str,
    period_from: date | None,
    period_to: date | None,
) -> AnalyticsRecalculationJob:
    """Record metric job.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        batch (DataUpdateBatch | None): Optional data update batch.
        job_type (str): Job type.
        period_from (date | None): Period start.
        period_to (date | None): Period end."""
    record = create_job(session, project_id, batch, job_type, period_from, period_to, 'v1')
    try:
        metrics = {'source_rows': count_period_rows(session, project_id, period_from, period_to)}
        return finish_job(session, record, 'completed', metrics, None)
    except Exception as error:
        return finish_job(session, record, 'failed', {}, str(error))


def run_signals_job(
    session: Session,
    project_id: UUID,
    batch: DataUpdateBatch | None,
    period_from: date | None,
    period_to: date | None,
    calculation_version: str,
) -> AnalyticsRecalculationJob:
    """Run signals job.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        batch (DataUpdateBatch | None): Optional data update batch.
        period_from (date | None): Period start.
        period_to (date | None): Period end.
        calculation_version (str): Calculation version."""
    record = create_job(session, project_id, batch, 'derived_signals', period_from, period_to, calculation_version)
    if period_from is None or period_to is None:
        return finish_job(session, record, 'skipped', {'reason': 'period_missing'}, None)
    try:
        response = recalculate_signals(
            session,
            str(project_id),
            RecalculateSignalsRequest(
                date_from=period_from,
                date_to=period_to,
                calculation_version=calculation_version,
            ),
        )
        return finish_job(session, record, 'completed', response.model_dump(mode='json'), None)
    except Exception as error:
        return finish_job(session, record, 'failed', {}, str(error))


def run_scoring_job(
    session: Session,
    project_id: UUID,
    batch: DataUpdateBatch | None,
    period_from: date | None,
    period_to: date | None,
    calculation_version: str,
) -> AnalyticsRecalculationJob:
    """Run scoring job.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        batch (DataUpdateBatch | None): Optional data update batch.
        period_from (date | None): Period start.
        period_to (date | None): Period end.
        calculation_version (str): Calculation version."""
    record = create_job(session, project_id, batch, 'opportunity_scores', period_from, period_to, calculation_version)
    if period_from is None or period_to is None:
        return finish_job(session, record, 'skipped', {'reason': 'period_missing'}, None)
    try:
        response = recalculate_scores(
            session,
            str(project_id),
            OpportunityScoreRecalculateRequest(
                date_from=period_from,
                date_to=period_to,
                calculation_version=calculation_version,
            ),
        )
        return finish_job(session, record, 'completed', response.model_dump(mode='json'), None)
    except Exception as error:
        return finish_job(session, record, 'failed', {}, str(error))


def update_freshness(session: Session, batch: DataUpdateBatch) -> DataFreshnessStatus:
    """Update freshness status.
    Args:
        session (Session): Active database session.
        batch (DataUpdateBatch): Data update batch."""
    latest_loaded = read_latest_loaded(session, batch.project_id, batch.source_type)
    latest_available = batch.period_to or latest_loaded
    lag_days = (latest_available - latest_loaded).days if latest_available and latest_loaded else None
    freshness_status = freshness_value(batch.status, latest_loaded, lag_days)
    record = session.scalar(
        select(DataFreshnessStatus).where(
            DataFreshnessStatus.project_id == batch.project_id,
            DataFreshnessStatus.dataset_type == batch.source_type,
        )
    )
    if record is None:
        record = DataFreshnessStatus(project_id=batch.project_id, dataset_type=batch.source_type)
        session.add(record)
    record.latest_available_date = latest_available
    record.latest_loaded_date = latest_loaded
    record.last_update_batch_id = batch.id
    record.freshness_status = freshness_status
    record.lag_days = lag_days
    record.updated_at = current_time()
    session.flush()
    return record


def read_latest_loaded(session: Session, project_id: UUID, dataset_type: str) -> date | None:
    """Read latest loaded date.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        dataset_type (str): Dataset type."""
    model = DATASET_MODELS.get(dataset_type)
    if model is None:
        return None
    return session.scalar(select(func.max(model.date)).where(model.project_id == project_id))


def read_period(
    session: Session,
    project_id: UUID,
    period_from: date | None,
    period_to: date | None,
) -> tuple[date | None, date | None]:
    """Read update period.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        period_from (date | None): Requested period start.
        period_to (date | None): Requested period end."""
    if period_from is not None and period_to is not None:
        return period_from, period_to
    row = session.execute(
        select(
            func.min(FactTrafficCountriesDaily.date).label('period_from'),
            func.max(FactTrafficCountriesDaily.date).label('period_to'),
        ).where(FactTrafficCountriesDaily.project_id == project_id)
    ).one()
    return period_from or row.period_from, period_to or row.period_to


def count_period_rows(
    session: Session,
    project_id: UUID,
    period_from: date | None,
    period_to: date | None,
) -> int:
    """Count period rows.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        period_from (date | None): Period start.
        period_to (date | None): Period end."""
    filters = [FactTrafficCountriesDaily.project_id == project_id]
    if period_from is not None:
        filters.append(FactTrafficCountriesDaily.date >= period_from)
    if period_to is not None:
        filters.append(FactTrafficCountriesDaily.date <= period_to)
    return int(session.scalar(select(func.count()).select_from(FactTrafficCountriesDaily).where(*filters)) or 0)


def ensure_rules(session: Session, project_id: UUID) -> list[AlertRule]:
    """Ensure alert rules.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier."""
    existing_types = set(
        session.scalars(select(AlertRule.alert_type).where(AlertRule.project_id == project_id)).all()
    )
    records: list[AlertRule] = []
    for alert_type, name, description, severity in DEFAULT_RULES:
        if alert_type in existing_types:
            continue
        record = AlertRule(
            project_id=project_id,
            alert_type=alert_type,
            name=name,
            description=description,
            severity_default=severity,
            is_enabled=True,
            threshold_json={'source': 'derived_analytics'},
            cooldown_hours=24,
            scope_json={},
        )
        session.add(record)
        records.append(record)
    session.commit()
    return records


def read_rules(session: Session, project_id: UUID) -> dict[str, AlertRule]:
    """Read alert rules.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier."""
    records = list(session.scalars(select(AlertRule).where(AlertRule.project_id == project_id)).all())
    return {record.alert_type: record for record in records}


def read_existing(session: Session, dedupe_key: str, cooldown_hours: int) -> AlertEvent | None:
    """Read existing alert.
    Args:
        session (Session): Active database session.
        dedupe_key (str): Alert dedupe key.
        cooldown_hours (int): Cooldown hours."""
    cutoff = current_time() - timedelta(hours=cooldown_hours)
    return session.scalar(
        select(AlertEvent)
        .where(AlertEvent.dedupe_key == dedupe_key, AlertEvent.detected_at >= cutoff)
        .order_by(AlertEvent.detected_at.desc())
        .limit(1)
    )


def build_dedupe(
    project_id: UUID,
    candidate: AlertCandidate,
    period_from: date | None,
    period_to: date | None,
) -> str:
    """Build dedupe key.
    Args:
        project_id (UUID): Project identifier.
        candidate (AlertCandidate): Alert candidate.
        period_from (date | None): Period start.
        period_to (date | None): Period end."""
    return ':'.join(
        [
            str(project_id),
            candidate.alert_type,
            str(candidate.country_id or 'all'),
            str(candidate.company_id or candidate.competitor_id or 'all'),
            str(candidate.channel or 'all'),
            str(period_from or 'none'),
            str(period_to or 'none'),
        ]
    )


def map_batch_status(status: str) -> str:
    """Map batch status.
    Args:
        status (str): Ingestion status."""
    if status == 'success':
        return 'completed'
    if status in {'partial_success', 'warning'}:
        return 'partial'
    if status in {'queued', 'pending'}:
        return 'pending'
    if status == 'running':
        return 'running'
    if status == 'cancelled':
        return 'cancelled'
    return 'failed'


def freshness_value(status: str, latest_loaded: date | None, lag_days: int | None) -> str:
    """Build freshness value.
    Args:
        status (str): Batch status.
        latest_loaded (date | None): Latest loaded date.
        lag_days (int | None): Lag days."""
    if status == 'failed':
        return 'failed'
    if latest_loaded is None:
        return 'missing'
    if lag_days is None or lag_days <= 1:
        return 'fresh'
    if lag_days <= 14:
        return 'stale'
    return 'missing'


def map_signal_type(record: DerivedSignal) -> str | None:
    """Map signal type.
    Args:
        record (DerivedSignal): Derived signal record."""
    if record.signal_type in {'new_activity', 'growth_acceleration'}:
        return 'traffic_spike'
    if record.signal_type in {'traffic_decline', 'forgotten_territory'}:
        return 'traffic_drop'
    if record.signal_type in {'new_territory', 'competitor_expansion'}:
        return 'competitor_new_country'
    if record.signal_type == 'traffic_quality_degradation':
        return 'traffic_quality_drop'
    if record.signal_type == 'channel_shift':
        channel = read_channel(record)
        if channel in {'paid', 'referral', 'social'}:
            return f'channel_spike_{channel}'
    if record.signal_type in {'low_noise_market', 'stable_market'}:
        return 'market_window'
    if normalize_severity(record.severity) in {'high', 'critical'}:
        return 'signal_severity_increase'
    return None


def read_channel(record: DerivedSignal) -> str | None:
    """Read signal channel.
    Args:
        record (DerivedSignal): Derived signal record."""
    details = record.details or {}
    channel = details.get('channel') or record.entity_id
    if channel is None:
        return None
    return str(channel)


def alert_title(alert_type: str, message: str) -> str:
    """Build alert title.
    Args:
        alert_type (str): Alert type.
        message (str): Alert message."""
    title = alert_type.replace('_', ' ').title()
    if message:
        return title
    return 'Market alert'


def normalize_severity(value: str | None) -> str:
    """Normalize severity.
    Args:
        value (str | None): Raw severity."""
    if value in SEVERITY_ORDER:
        return value
    return 'medium'


def higher_severity(first_value: str, second_value: str) -> str:
    """Read higher severity.
    Args:
        first_value (str): First severity.
        second_value (str): Second severity."""
    first = normalize_severity(first_value)
    second = normalize_severity(second_value)
    return first if SEVERITY_ORDER[first] >= SEVERITY_ORDER[second] else second


def merge_values(first_values: list[Any], second_values: list[Any]) -> list[Any]:
    """Merge JSON values.
    Args:
        first_values (list[Any]): Existing values.
        second_values (list[Any]): Incoming values."""
    values: list[Any] = []
    seen_values: set[str] = set()
    for item in [*first_values, *second_values]:
        key = str(item)
        if key in seen_values:
            continue
        seen_values.add(key)
        values.append(item)
    return values
