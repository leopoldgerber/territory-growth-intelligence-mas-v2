from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base
from app.models import tables


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
settings = get_settings()
config.set_main_option('sqlalchemy.url', settings.database_url)
tables_metadata = tables


def run_offline_migrations() -> bool:
    """Run migrations in offline mode.
    Args:
        None (None): No arguments are required."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()

    return True


def run_online_migrations() -> bool:
    """Run migrations in online mode.
    Args:
        None (None): No arguments are required."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    return True


if context.is_offline_mode():
    migration_result = run_offline_migrations()
else:
    migration_result = run_online_migrations()
