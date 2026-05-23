from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_session


router = APIRouter(prefix='/db', tags=['database'])


@router.get('/health')
def read_db_health(session: Session = Depends(get_session)) -> dict[str, str | float]:
    """Read database health.
    Args:
        session (Session): Active database session."""
    settings = get_settings()
    start_time = perf_counter()
    session.execute(text('select 1'))
    latency_ms = round((perf_counter() - start_time) * 1000, 2)
    health_data = {
        'status': 'ok',
        'database': settings.postgres_db,
        'latency_ms': latency_ms,
    }
    return health_data
