import os
import sys

# Add project root to sys.path
# Assuming env.py is in apps/backend/alembic, to get to apps/backend:
alembic_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(alembic_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root) # Insert at the beginning

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context  # type: ignore
from src.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config #noqa: E1101

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    db_url_for_alembic = settings.ASYNC_DATABASE_URL
    if "postgresql+asyncpg://" in db_url_for_alembic:
        db_url_for_alembic = db_url_for_alembic.replace("postgresql+asyncpg://", "postgresql://")
    elif "postgresql+asyncpg:" in db_url_for_alembic: # DSN style without //
        db_url_for_alembic = db_url_for_alembic.replace("postgresql+asyncpg:", "postgresql:")

    config.set_main_option("sqlalchemy.url", db_url_for_alembic)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
