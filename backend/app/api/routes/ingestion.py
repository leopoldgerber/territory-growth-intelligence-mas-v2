from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_session
from app.ingestion.audit import get_errors, get_run, list_runs
from app.ingestion.schemas import list_types
from app.ingestion.service import accept_upload, serialize_error, serialize_run

router = APIRouter(prefix='/ingestion', tags=['ingestion'])


@router.get('/file-types')
def read_file_types() -> dict[str, list[str]]:
    """Read supported ingestion file types.
    Args:
        None (None): No arguments are required."""
    file_types = list_types()
    return {'file_types': file_types}


@router.post('/upload')
async def upload_file(
    file_type: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, object]:
    """Upload ingestion file.
    Args:
        file_type (str): Ingestion file type.
        file (UploadFile): Uploaded CSV or XLSX file.
        session (Session): Active database session."""
    settings = get_settings()
    project_id = UUID(settings.default_project_id)
    file_content = await file.read()
    file_name = file.filename or 'uploaded_file'
    result = accept_upload(session, project_id, file_type, file_name, file_content)
    return result


@router.get('/runs')
def read_runs(
    session: Annotated[Session, Depends(get_session)],
    limit: int = 20,
) -> dict[str, list[dict[str, object]]]:
    """Read ingestion runs.
    Args:
        session (Session): Active database session.
        limit (int): Maximum run count."""
    runs = [serialize_run(ingestion_run) for ingestion_run in list_runs(session, limit)]
    return {'runs': runs}


@router.get('/runs/{run_id}')
def read_run(run_id: UUID, session: Annotated[Session, Depends(get_session)]) -> dict[str, object]:
    """Read ingestion run.
    Args:
        run_id (UUID): Ingestion run identifier.
        session (Session): Active database session."""
    ingestion_run = get_run(session, run_id)
    if ingestion_run is None:
        raise HTTPException(status_code=404, detail='Ingestion run not found')
    run_data = serialize_run(ingestion_run)
    return run_data


@router.get('/runs/{run_id}/errors')
def read_errors(
    run_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, list[dict[str, object]]]:
    """Read ingestion validation errors.
    Args:
        run_id (UUID): Ingestion run identifier.
        session (Session): Active database session."""
    errors = [serialize_error(error) for error in get_errors(session, run_id)]
    return {'errors': errors}
