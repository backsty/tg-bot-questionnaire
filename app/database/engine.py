from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import DATABASE_URL, DEBUG

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,
)

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