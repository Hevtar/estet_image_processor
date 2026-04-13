"""
Response schemas.
"""
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductResult(BaseModel):
    """Результат поиска - один продукт"""
    id: UUID
    name: str
    category: str
    style: Optional[str]
    color_family: Optional[str]
    ai_semantic_description: Optional[str]
    main_image_url: Optional[str]
    product_url: Optional[str]
    score: float = Field(..., description="Релевантность (0-1)")


class SearchResponse(BaseModel):
    """Ответ на поиск"""
    success: bool = True
    results: List[ProductResult] = []
    total: int = 0
    analysis: Optional[Dict] = Field(None, description="Результат анализа изображения")
    message: Optional[str] = None
