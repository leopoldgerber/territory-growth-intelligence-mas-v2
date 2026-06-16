from pathlib import Path
from uuid import UUID

from app.core.config import ROOT_DIR, get_settings


def clean_filename(file_name: str) -> str:
    """Clean uploaded file name.
    Args:
        file_name (str): Uploaded file name."""
    cleaned_name = Path(file_name).name.strip()
    if cleaned_name == '':
        cleaned_name = 'uploaded_file'
    return cleaned_name


def storage_path() -> Path:
    """Resolve upload storage path.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    upload_path = Path(settings.upload_storage_path)
    if not upload_path.is_absolute():
        upload_path = ROOT_DIR / upload_path
    return upload_path


def save_upload(run_id: UUID, file_name: str, file_content: bytes) -> str:
    """Save uploaded file.
    Args:
        run_id (UUID): Ingestion run identifier.
        file_name (str): Uploaded file name.
        file_content (bytes): Uploaded file content."""
    upload_root = storage_path()
    run_directory = upload_root / str(run_id)
    run_directory.mkdir(parents=True, exist_ok=True)
    stored_path = run_directory / clean_filename(file_name)
    stored_path.write_bytes(file_content)
    return str(stored_path)


def open_file(stored_file_path: str) -> bytes:
    """Open stored upload file.
    Args:
        stored_file_path (str): Stored upload file path."""
    file_content = Path(stored_file_path).read_bytes()
    return file_content


def delete_file(stored_file_path: str) -> bool:
    """Delete stored upload file.
    Args:
        stored_file_path (str): Stored upload file path."""
    file_path = Path(stored_file_path)
    if not file_path.exists():
        return False
    file_path.unlink()
    return True
