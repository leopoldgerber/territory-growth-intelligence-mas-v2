from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.tables import (
    FactDeviceTrendsDaily,
    FactJourneySourcesDaily,
    FactTrafficCountriesDaily,
    FactTrafficSourcesDaily,
    IngestionRun,
    IngestionValidationError,
)

FACT_MODELS = {
    'traffic_countries': FactTrafficCountriesDaily,
    'traffic_sources': FactTrafficSourcesDaily,
    'journey_sources': FactJourneySourcesDaily,
    'trend_by_devices': FactDeviceTrendsDaily,
}


def create_run(
    session: Session,
    project_id: UUID,
    file_name: str,
    file_type: str,
    file_extension: str,
    file_size_bytes: int,
    checksum: str,
    stored_file_path: str | None = None,
) -> IngestionRun:
    """Create ingestion audit run.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        file_name (str): Uploaded file name.
        file_type (str): Ingestion file type.
        file_extension (str): Uploaded file extension.
        file_size_bytes (int): Uploaded file size in bytes.
        checksum (str): Uploaded file checksum.
        stored_file_path (str | None): Stored upload path."""
    ingestion_run = IngestionRun(
        id=uuid4(),
        project_id=project_id,
        file_name=file_name,
        file_type=file_type,
        file_extension=file_extension,
        file_size_bytes=file_size_bytes,
        source_kind='upload',
        stored_file_path=stored_file_path,
        checksum=checksum,
        row_count=0,
        valid_row_count=0,
        invalid_row_count=0,
        inserted_row_count=0,
        skipped_duplicate_count=0,
        failed_row_count=0,
        status='pending',
        ingestion_status='pending',
        validation_status='not_started',
        progress_stage='accepted',
        progress_percent=0,
    )
    session.add(ingestion_run)
    session.flush()
    return ingestion_run


def update_run(session: Session, ingestion_run: IngestionRun, values: dict[str, Any]) -> IngestionRun:
    """Update ingestion audit run.
    Args:
        session (Session): Active database session.
        ingestion_run (IngestionRun): Ingestion run model.
        values (dict[str, Any]): Updated run values."""
    for field_name, field_value in values.items():
        setattr(ingestion_run, field_name, field_value)
    ingestion_run.updated_at = datetime.now(UTC)
    session.add(ingestion_run)
    session.flush()
    return ingestion_run


def mark_queued(session: Session, ingestion_run: IngestionRun) -> IngestionRun:
    """Mark ingestion run as queued.
    Args:
        session (Session): Active database session.
        ingestion_run (IngestionRun): Ingestion run model."""
    queued_run = update_run(
        session,
        ingestion_run,
        {
            'status': 'queued',
            'ingestion_status': 'queued',
            'validation_status': 'not_started',
            'progress_stage': 'queued',
            'progress_percent': 5,
            'queued_at': datetime.now(UTC),
        },
    )
    return queued_run


def update_stage(
    session: Session,
    ingestion_run: IngestionRun,
    progress_stage: str,
    progress_percent: float,
    validation_status: str | None = None,
) -> IngestionRun:
    """Update ingestion progress stage.
    Args:
        session (Session): Active database session.
        ingestion_run (IngestionRun): Ingestion run model.
        progress_stage (str): Current progress stage.
        progress_percent (float): Current progress percent.
        validation_status (str | None): Optional validation status."""
    values = {
        'progress_stage': progress_stage,
        'progress_percent': progress_percent,
    }
    if validation_status is not None:
        values['validation_status'] = validation_status
    staged_run = update_run(session, ingestion_run, values)
    return staged_run


def find_duplicate_run(session: Session, file_type: str, checksum: str) -> IngestionRun | None:
    """Find successful run by file checksum.
    Args:
        session (Session): Active database session.
        file_type (str): Ingestion file type.
        checksum (str): Uploaded file checksum."""
    terminal_statuses = ['success', 'partial_success']
    statement = (
        select(IngestionRun)
        .where(
            IngestionRun.file_type == file_type,
            IngestionRun.checksum == checksum,
            IngestionRun.status.in_(terminal_statuses),
        )
        .order_by(IngestionRun.created_at.desc())
    )
    ingestion_run = None
    for candidate_run in session.scalars(statement).all():
        if count_fact_rows(session, candidate_run) > 0:
            ingestion_run = candidate_run
            break
    return ingestion_run


def count_fact_rows(session: Session, ingestion_run: IngestionRun) -> int:
    """Count fact rows for ingestion run.
    Args:
        session (Session): Active database session.
        ingestion_run (IngestionRun): Ingestion run model."""
    fact_model = FACT_MODELS.get(ingestion_run.file_type)
    if fact_model is None:
        return 0
    statement = select(func.count()).select_from(fact_model).where(fact_model.ingestion_run_id == ingestion_run.id)
    fact_count = int(session.scalar(statement) or 0)
    return fact_count


def finish_run(session: Session, ingestion_run: IngestionRun, summary: dict[str, Any]) -> IngestionRun:
    """Finish ingestion audit run.
    Args:
        session (Session): Active database session.
        ingestion_run (IngestionRun): Ingestion run model.
        summary (dict[str, Any]): Ingestion summary values."""
    for field_name, field_value in summary.items():
        setattr(ingestion_run, field_name, field_value)
    ingestion_run.progress_stage = summary.get('progress_stage', 'completed')
    ingestion_run.progress_percent = summary.get('progress_percent', 100)
    ingestion_run.updated_at = datetime.now(UTC)
    ingestion_run.finished_at = datetime.now(UTC)
    session.add(ingestion_run)
    session.flush()
    return ingestion_run


def fail_run(session: Session, ingestion_run_id: UUID, error_message: str) -> int:
    """Mark ingestion run as failed.
    Args:
        session (Session): Active database session.
        ingestion_run_id (UUID): Ingestion run identifier.
        error_message (str): Run-level error message."""
    statement = (
        update(IngestionRun)
        .where(IngestionRun.id == ingestion_run_id)
        .values(
            status='failed',
            ingestion_status='failed',
            validation_status='failed',
            progress_stage='failed',
            progress_percent=100,
            error_message=error_message,
            finished_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    result = session.execute(statement)
    session.flush()
    return result.rowcount or 0


def write_errors(session: Session, ingestion_run_id: UUID, errors: list[Any]) -> list[IngestionValidationError]:
    """Write ingestion validation errors.
    Args:
        session (Session): Active database session.
        ingestion_run_id (UUID): Ingestion run identifier.
        errors (list[Any]): Validation error objects."""
    error_models = []
    for error in errors:
        error_model = IngestionValidationError(
            ingestion_run_id=ingestion_run_id,
            row_number=error.row_number,
            column_name=error.column_name,
            error_code=error.error_code,
            error_message=error.error_message,
            raw_value=error.raw_value,
        )
        session.add(error_model)
        error_models.append(error_model)
    session.flush()
    return error_models


def list_runs(session: Session, limit: int) -> list[IngestionRun]:
    """List ingestion runs.
    Args:
        session (Session): Active database session.
        limit (int): Maximum runs count."""
    statement = select(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(limit)
    runs = list(session.scalars(statement).all())
    return runs


def get_run(session: Session, run_id: UUID) -> IngestionRun | None:
    """Get ingestion run.
    Args:
        session (Session): Active database session.
        run_id (UUID): Ingestion run identifier."""
    ingestion_run = session.get(IngestionRun, run_id)
    return ingestion_run


def get_errors(session: Session, run_id: UUID) -> list[IngestionValidationError]:
    """Get ingestion validation errors.
    Args:
        session (Session): Active database session.
        run_id (UUID): Ingestion run identifier."""
    statement = (
        select(IngestionValidationError)
        .where(IngestionValidationError.ingestion_run_id == run_id)
        .order_by(IngestionValidationError.row_number.asc())
    )
    errors = list(session.scalars(statement).all())
    return errors
