"""
Database connection и session management.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self, database_url: str, echo: bool = False):
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=NullPool,  # Для async лучше без пула
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager для сессии"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise

    async def close(self):
        """Закрыть соединение"""
        await self.engine.dispose()

    async def create_tables(self):
        """Создать все таблицы"""
        from estet_shared.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created")

    async def drop_tables(self):
        """Удалить все таблицы (ОСТОРОЖНО!)"""
        from estet_shared.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("⚠️ Database tables dropped")
