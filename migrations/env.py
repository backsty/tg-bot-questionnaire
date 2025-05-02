import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# импорт моделей и базы
from app.database.base import Base
# импортируем все модели, чтобы они были доступны для автогенерации
from app.database.models.user import User
from app.config import POSTGRES_URI, PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DB


# эта строка гарантирует, что переменные из alembic.ini доступны
config = context.config

# Устанавливаем параметры подключения к БД из окружения
config.set_main_option("sqlalchemy.url", f"postgresql+asyncpg://{POSTGRES_URI.split('://', 1)[1]}")

# Загружаем файл конфигурации логирования, если он указан
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# здесь указываем целевую метаинформацию (модели) для автогенерации миграций
target_metadata = Base.metadata

# другие значения из конфига, определяемые пользователем, можно передать
# в context


def run_migrations_offline() -> None:
    """Запуск миграций в 'офлайн' режиме.

    Не требует подключения к БД.
    Конфигурация поступает исключительно из alembic.ini.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """В этой функции запускаются все миграции в асинхронном контексте."""

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запускает миграции в онлайн режиме."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()