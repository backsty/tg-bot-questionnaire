from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import POSTGRES_URI

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    f"postgresql+asyncpg://{POSTGRES_URI.split('://', 1)[1]}",
    echo=False,
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