import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.core.config import get_settings


def configure_queue() -> RedisBroker:
    """Configure ingestion queue.
    Args:
        None (None): No arguments are required."""
    settings = get_settings()
    broker = RedisBroker(url=settings.redis_url)
    dramatiq.set_broker(broker)
    return broker


def enqueue_run(run_id: str) -> str:
    """Enqueue ingestion run.
    Args:
        run_id (str): Ingestion run identifier."""
    from app.ingestion.tasks import process_ingestion

    message = process_ingestion.send(run_id)
    return message.message_id
