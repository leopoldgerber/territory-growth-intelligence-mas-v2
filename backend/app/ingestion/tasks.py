from uuid import UUID

import dramatiq

from app.core.database import SessionLocal
from app.ingestion.queue import configure_queue
from app.ingestion.service import process_run

configure_queue()


@dramatiq.actor(max_retries=3)
def process_ingestion(run_id: str) -> str:
    """Process queued ingestion run.
    Args:
        run_id (str): Ingestion run identifier."""
    session = SessionLocal()
    try:
        process_run(session, UUID(run_id))
        session.commit()
    finally:
        session.close()
    return run_id
