from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding='utf-8')

    app_name: str = 'Territory Growth Intelligence'
    app_env: str = 'local'
    app_version: str = '0.1.0'
    cors_origins: str = 'http://localhost:3000'
    default_project_id: str = '00000000-0000-0000-0000-000000000001'
    postgres_db: str = 'tgi_local'
    postgres_user: str = 'tgi_user'
    postgres_password: str = 'tgi_password'
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    database_url: str = 'postgresql+psycopg://tgi_user:tgi_password@localhost:5432/tgi_local'
    redis_url: str = 'redis://localhost:6379/0'
    upload_storage_backend: str = 'local'
    upload_storage_path: str = 'backend/storage/uploads'
    ingestion_max_file_size_mb: int = 500
    ingestion_poll_interval_seconds: int = 3
    llm_provider: str = 'disabled'
    llm_model: str = ''
    llm_base_url: str = ''
    llm_api_key: str = ''
    llm_timeout_seconds: int = 60
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4000
    llm_retry_attempts: int = 2
    llm_retry_backoff_ms: int = 1000
    llm_structured_output: bool = True
    vectorstore_provider: str = 'qdrant'
    qdrant_url: str = 'http://localhost:6333'
    qdrant_api_key: str = ''
    qdrant_collection: str = 'tgi_knowledge_v1'
    embedding_provider: str = 'disabled'
    embedding_model: str = ''
    embedding_dimensions: int = 0
    embedding_timeout_seconds: int = 60
    embedding_retry_attempts: int = 2
    embedding_retry_backoff_ms: int = 1000
    rag_chunk_size_chars: int = 4000
    rag_chunk_overlap_chars: int = 500


@lru_cache
def get_settings() -> Settings:
    """Load application settings.
    Args:
        None (None): No arguments are required."""
    settings = Settings()
    return settings
