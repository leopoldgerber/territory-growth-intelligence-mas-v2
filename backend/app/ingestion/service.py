from datetime import UTC, datetime
from hashlib import sha256
from socket import gethostname
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestion.audit import (
    create_run,
    fail_run,
    finish_run,
    get_run,
    mark_queued,
    update_run,
    update_stage,
    write_errors,
)
from app.ingestion.loaders import load_rows
from app.ingestion.readers import get_extension, read_upload
from app.ingestion.schemas import ALLOWED_EXTENSIONS, FILE_SCHEMAS, get_schema
from app.ingestion.storage import open_file, save_upload
from app.ingestion.validators import ValidationError, validate_data


def calculate_checksum(file_content: bytes) -> str:
    """Calculate file checksum.
    Args:
        file_content (bytes): Uploaded file content."""
    checksum = sha256(file_content).hexdigest()
    return checksum


def accept_upload(
    session: Session,
    project_id: UUID,
    file_type: str,
    file_name: str,
    file_content: bytes,
) -> dict[str, Any]:
    """Accept upload for async ingestion.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        file_type (str): Ingestion file type.
        file_name (str): Uploaded file name.
        file_content (bytes): Uploaded file content."""
    file_extension = get_extension(file_name)
    checksum = calculate_checksum(file_content)
    ingestion_run = create_run(
        session=session,
        project_id=project_id,
        file_name=file_name,
        file_type=file_type,
        file_extension=file_extension,
        file_size_bytes=len(file_content),
        checksum=checksum,
    )

    initial_error = validate_upload(file_type, file_extension, file_content)
    if initial_error is not None:
        finish_run(session, ingestion_run, fail_summary(initial_error))
        write_errors(session, ingestion_run.id, [build_global_error(initial_error)])
        session.commit()
        return accepted_response(ingestion_run.id, 'failed', initial_error)

    stored_file_path = save_upload(ingestion_run.id, file_name, file_content)
    update_run(session, ingestion_run, {'stored_file_path': stored_file_path})
    mark_queued(session, ingestion_run)
    session.commit()

    try:
        from app.ingestion.queue import enqueue_run

        enqueue_run(str(ingestion_run.id))
    except Exception as error:
        fail_run(session, ingestion_run.id, str(error))
        write_errors(session, ingestion_run.id, [build_global_error(str(error))])
        session.commit()
        return accepted_response(ingestion_run.id, 'failed', str(error))

    return accepted_response(ingestion_run.id, 'queued', 'File accepted and queued for ingestion')


def process_run(session: Session, run_id: UUID) -> dict[str, Any]:
    """Process queued ingestion run.
    Args:
        session (Session): Active database session.
        run_id (UUID): Ingestion run identifier."""
    ingestion_run = get_run(session, run_id)
    if ingestion_run is None:
        return {'run_id': str(run_id), 'status': 'failed', 'message': 'Ingestion run not found'}

    try:
        update_run(
            session,
            ingestion_run,
            {
                'status': 'running',
                'ingestion_status': 'running',
                'worker_name': gethostname(),
                'started_at': now_value(),
            },
        )
        session.commit()
        file_content = read_stored(ingestion_run.stored_file_path)
        update_stage(session, ingestion_run, 'reading_file', 15)
        data = read_upload(ingestion_run.file_name, file_content, ingestion_run.file_type)
        session.commit()
        update_stage(session, ingestion_run, 'normalizing', 30)
        schema = get_schema(ingestion_run.file_type)
        session.commit()
        update_stage(session, ingestion_run, 'validating_schema', 45, 'running')
        validation_result = validate_data(data, schema)
        write_errors(session, ingestion_run.id, validation_result.errors)
        session.commit()
        if not validation_result.valid_rows and validation_result.errors:
            summary = validation_failure_summary(validation_result.row_count, validation_result.errors)
            finish_run(session, ingestion_run, summary)
            session.commit()
            return serialize_run(ingestion_run)
        update_stage(session, ingestion_run, 'checking_duplicates', 60)
        session.commit()
        update_stage(session, ingestion_run, 'loading_dimensions', 72)
        session.commit()
        update_stage(session, ingestion_run, 'loading_facts', 84)
        load_summary = load_rows(
            session=session,
            file_type=ingestion_run.file_type,
            project_id=ingestion_run.project_id,
            ingestion_run_id=ingestion_run.id,
            rows=validation_result.valid_rows,
            source_file_name=ingestion_run.file_name,
        )
        summary = success_summary(
            validation_result.row_count,
            len(validation_result.valid_rows),
            validation_result.errors,
        )
        summary.update(load_summary)
        summary = apply_warning(summary)
        update_stage(session, ingestion_run, 'writing_audit', 96)
        finish_run(session, ingestion_run, summary)
        session.commit()
    except Exception as error:
        session.rollback()
        fail_run(session, run_id, str(error))
        write_errors(session, run_id, [build_global_error(str(error))])
        session.commit()

    refreshed_run = get_run(session, run_id)
    if refreshed_run is None:
        return {'run_id': str(run_id), 'status': 'failed', 'message': 'Ingestion run not found'}
    return serialize_run(refreshed_run)


def upload_data(
    session: Session,
    project_id: UUID,
    file_type: str,
    file_name: str,
    file_content: bytes,
) -> dict[str, Any]:
    """Upload ingestion data.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        file_type (str): Ingestion file type.
        file_name (str): Uploaded file name.
        file_content (bytes): Uploaded file content."""
    accepted_run = accept_upload(session, project_id, file_type, file_name, file_content)
    return accepted_run


def validate_upload(file_type: str, file_extension: str, file_content: bytes) -> str | None:
    """Validate upload metadata.
    Args:
        file_type (str): Ingestion file type.
        file_extension (str): Uploaded file extension.
        file_content (bytes): Uploaded file content."""
    settings = get_settings()
    max_size_bytes = settings.ingestion_max_file_size_mb * 1024 * 1024
    if file_type not in FILE_SCHEMAS:
        return f'Unsupported file type: {file_type}'
    if file_extension not in ALLOWED_EXTENSIONS:
        return 'Unsupported file extension'
    if len(file_content) > max_size_bytes:
        return 'Uploaded file is larger than allowed limit'
    return None


def read_stored(stored_file_path: str | None) -> bytes:
    """Read stored upload content.
    Args:
        stored_file_path (str | None): Stored upload path."""
    if stored_file_path is None:
        raise ValueError('Stored file path is empty')
    file_content = open_file(stored_file_path)
    return file_content


def accepted_response(run_id: UUID, status: str, message: str) -> dict[str, Any]:
    """Build upload acceptance response.
    Args:
        run_id (UUID): Ingestion run identifier.
        status (str): Current ingestion status.
        message (str): Response message."""
    response = {
        'run_id': str(run_id),
        'status': status,
        'message': message,
    }
    return response


def fail_summary(error_message: str) -> dict[str, Any]:
    """Build failed ingestion summary.
    Args:
        error_message (str): Ingestion error message."""
    summary = {
        'status': 'failed',
        'ingestion_status': 'failed',
        'validation_status': 'failed',
        'progress_stage': 'failed',
        'progress_percent': 100,
        'error_message': error_message,
    }
    return summary


def build_global_error(error_message: str) -> ValidationError:
    """Build global ingestion error.
    Args:
        error_message (str): Ingestion error message."""
    validation_error = ValidationError(
        row_number=0,
        column_name='file',
        error_code='ingestion_failed',
        error_message=error_message,
        raw_value=None,
    )
    return validation_error


def success_summary(row_count: int, valid_row_count: int, errors: list[Any]) -> dict[str, Any]:
    """Build successful ingestion summary.
    Args:
        row_count (int): Source row count.
        valid_row_count (int): Valid row count.
        errors (list[Any]): Validation errors."""
    invalid_row_count = len({error.row_number for error in errors if error.row_number > 0})
    validation_status = 'success' if not errors else 'warning'
    summary = {
        'row_count': row_count,
        'valid_row_count': valid_row_count,
        'invalid_row_count': invalid_row_count,
        'failed_row_count': 0,
        'status': 'success',
        'ingestion_status': 'success',
        'validation_status': validation_status,
        'progress_stage': 'completed',
        'progress_percent': 100,
        'error_message': None,
    }
    return summary


def validation_failure_summary(row_count: int, errors: list[Any]) -> dict[str, Any]:
    """Build failed validation summary.
    Args:
        row_count (int): Source row count.
        errors (list[Any]): Validation errors."""
    invalid_rows = {error.row_number for error in errors if error.row_number > 0}
    invalid_row_count = len(invalid_rows) if invalid_rows else row_count
    summary = {
        'row_count': row_count,
        'valid_row_count': 0,
        'invalid_row_count': invalid_row_count,
        'inserted_row_count': 0,
        'skipped_duplicate_count': 0,
        'failed_row_count': invalid_row_count,
        'status': 'failed',
        'ingestion_status': 'failed',
        'validation_status': 'failed',
        'progress_stage': 'failed',
        'progress_percent': 100,
        'error_message': 'Uploaded file does not match selected file type',
    }
    return summary


def apply_warning(summary: dict[str, Any]) -> dict[str, Any]:
    """Apply warning status to ingestion summary.
    Args:
        summary (dict[str, Any]): Ingestion summary values."""
    duplicate_count = summary.get('skipped_duplicate_count') or 0
    invalid_count = summary.get('invalid_row_count') or 0
    if duplicate_count > 0 or invalid_count > 0:
        summary['status'] = 'partial_success'
        summary['ingestion_status'] = 'warning'
        summary['validation_status'] = 'warning'
    return summary


def serialize_run(ingestion_run: Any) -> dict[str, Any]:
    """Serialize ingestion run.
    Args:
        ingestion_run (Any): Ingestion run model."""
    run_data = {
        'id': str(ingestion_run.id),
        'run_id': str(ingestion_run.id),
        'project_id': str(ingestion_run.project_id),
        'file_name': ingestion_run.file_name,
        'file_type': ingestion_run.file_type,
        'file_extension': ingestion_run.file_extension,
        'file_size_bytes': ingestion_run.file_size_bytes,
        'checksum': ingestion_run.checksum,
        'stored_file_path': ingestion_run.stored_file_path,
        'status': ingestion_run.status,
        'progress_stage': ingestion_run.progress_stage,
        'progress_percent': float(ingestion_run.progress_percent or 0),
        'period_start': serialize_value(ingestion_run.period_start),
        'period_end': serialize_value(ingestion_run.period_end),
        'row_count': ingestion_run.row_count,
        'valid_row_count': ingestion_run.valid_row_count,
        'invalid_row_count': ingestion_run.invalid_row_count,
        'inserted_row_count': ingestion_run.inserted_row_count,
        'skipped_duplicate_count': ingestion_run.skipped_duplicate_count,
        'failed_row_count': ingestion_run.failed_row_count,
        'company_count': ingestion_run.company_count,
        'domain_count': ingestion_run.domain_count,
        'country_count': ingestion_run.country_count,
        'ingestion_status': ingestion_run.ingestion_status,
        'validation_status': ingestion_run.validation_status,
        'error_message': ingestion_run.error_message,
        'worker_name': ingestion_run.worker_name,
        'created_at': serialize_value(ingestion_run.created_at),
        'updated_at': serialize_value(ingestion_run.updated_at),
        'queued_at': serialize_value(ingestion_run.queued_at),
        'started_at': serialize_value(ingestion_run.started_at),
        'finished_at': serialize_value(ingestion_run.finished_at),
    }
    return run_data


def serialize_error(error: Any) -> dict[str, Any]:
    """Serialize validation error.
    Args:
        error (Any): Validation error model."""
    error_data = {
        'id': error.id,
        'ingestion_run_id': str(error.ingestion_run_id),
        'row_number': error.row_number,
        'column_name': error.column_name,
        'error_code': error.error_code,
        'error_message': error.error_message,
        'raw_value': error.raw_value,
        'created_at': serialize_value(error.created_at),
    }
    return error_data


def serialize_value(value: Any) -> str | None:
    """Serialize date-like value.
    Args:
        value (Any): Date-like value."""
    if value is None:
        return None
    serialized_value = value.isoformat()
    return serialized_value


def now_value() -> datetime:
    """Read current timestamp.
    Args:
        None (None): No arguments are required."""
    current_time = datetime.now(UTC)
    return current_time
