from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def create_engine_instance(database_url: str) -> Engine:
    """Create SQLAlchemy engine.
    Args:
        database_url (str): Database connection URL."""
    engine = create_engine(database_url, pool_pre_ping=True)
    return engine


settings = get_settings()
engine = create_engine_instance(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Provide database session.
    Args:
        None (None): No arguments are required."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
