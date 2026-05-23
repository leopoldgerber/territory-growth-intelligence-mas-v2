from fastapi import APIRouter, Depends
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.database import get_session


router = APIRouter(prefix='/meta', tags=['metadata'])


@router.get('/tables')
def read_tables(session: Session = Depends(get_session)) -> dict[str, list[str] | str]:
    """Read database table names.
    Args:
        session (Session): Active database session."""
    inspector = inspect(session.bind)
    table_names = inspector.get_table_names()
    tables_data = {
        'schema': 'public',
        'tables': table_names,
    }
    return tables_data
