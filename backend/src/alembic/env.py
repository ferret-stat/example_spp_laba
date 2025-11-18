import os
from logging.config import fileConfig
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine.url import make_url
from alembic import context

from src.database.models import Base

load_dotenv()

config = context.config

database_url = os.getenv("POSTGRES_URL")


def create_database_if_not_exists(url: str):
    parsed_url = make_url(url)
    db_name = parsed_url.database
    tmp_url = parsed_url.set(database="postgres")
    engine = create_engine(tmp_url)

    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
        )
        exists = result.scalar() is not None

    if not exists:
        print(f"Creating database {db_name}...")
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                text(f"CREATE DATABASE {db_name}")
            )


create_database_if_not_exists(database_url)

config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    """Offline mode: только генерация SQL."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Online mode: реально подключаемся и применяем миграции."""
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
