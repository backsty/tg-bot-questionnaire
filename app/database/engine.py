from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging

from app.config import DATABASE_URL

# Настройка логирования
logger = logging.getLogger(__name__)

# Создание асинхронного движка SQLAlchemy
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,  # Оптимальный размер пула соединений
        max_overflow=10,  # Максимальное количество дополнительных соединений
    )
    logger.info(f"Создан движок базы данных для {DATABASE_URL.split('@')[1]}")
except Exception as e:
    logger.error(f"Ошибка создания движка БД: {e}")
    raise

# Создание фабрики сессий
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор сессий базы данных
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()