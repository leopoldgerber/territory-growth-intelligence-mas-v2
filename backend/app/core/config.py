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
    postgres_db: str = 'tgi_local'
    postgres_user: str = 'tgi_user'
    postgres_password: str = 'tgi_password'
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    database_url: str = 'postgresql+psycopg://tgi_user:tgi_password@localhost:5432/tgi_local'


@lru_cache
def get_settings() -> Settings:
    """Load application settings.
    Args:
        None (None): No arguments are required."""
    settings = Settings()
    return settings
