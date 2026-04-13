"""
API dependencies.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from estet_shared.database import Database
from ..config import settings


def get_db_session():
    """Dependency для получения DB сессии"""
    db = Database(settings.DATABASE_URL)
    return db


async def get_session(db: Database = Depends(get_db_session)) -> AsyncSession:
    """Dependency для получения асинхронной сессии"""
    async with db.session() as session:
        yield session
