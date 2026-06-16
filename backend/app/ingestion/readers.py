from io import BytesIO
from pathlib import Path
from typing import Any

from app.ingestion.normalizers import normalize_column
from app.ingestion.schemas import ALLOWED_EXTENSIONS


def read_upload(file_name: str, file_content: bytes, file_type: str | None = None) -> Any:
    """Read uploaded tabular file.
    Args:
        file_name (str): Uploaded file name.
        file_content (bytes): Uploaded file content.
        file_type (str | None): Optional ingestion file type."""
    import pandas as pd

    file_extension = Path(file_name).suffix.lower()
    if file_extension == '.csv':
        data = pd.read_csv(BytesIO(file_content))
    elif file_extension == '.xlsx':
        data = pd.read_excel(BytesIO(file_content))
    else:
        allowed_text = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f'Unsupported file extension. Allowed extensions: {allowed_text}')

    data.columns = [normalize_column(str(column_name)) for column_name in data.columns]
    data = apply_aliases(data, file_type)
    return data


def apply_aliases(data: Any, file_type: str | None) -> Any:
    """Apply file-specific column aliases.
    Args:
        data (pd.DataFrame): Uploaded dataframe.
        file_type (str | None): Optional ingestion file type."""
    if file_type == 'journey_sources' and 'search' in data.columns and 'search_source' not in data.columns:
        data = data.rename(columns={'search': 'search_source'})
    return data


def get_extension(file_name: str) -> str:
    """Get file extension.
    Args:
        file_name (str): Uploaded file name."""
    file_extension = Path(file_name).suffix.lower()
    return file_extension
