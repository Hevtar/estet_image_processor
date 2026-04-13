"""
Request schemas.
"""
from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Запрос на поиск по тексту"""
    query: str = Field(..., description="Текстовый запрос", min_length=3)
    max_results: int = Field(10, ge=1, le=50, description="Максимум результатов")
    category: Optional[str] = Field(None, description="Фильтр по категории")
    style: Optional[str] = Field(None, description="Фильтр по стилю")
