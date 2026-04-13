"""
Модели для векторных представлений.
"""
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base


class ProductEmbedding(Base):
    """Векторное представление продукта"""
    __tablename__ = "product_embeddings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))

    # Вектор (768 dimensions для Gemini embeddings)
    embedding = Column(Vector(768), nullable=False)

    embedding_type = Column(String(50), default="semantic")
    model_version = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="embeddings")


class EmbeddingCreate(BaseModel):
    """Схема для создания embedding"""
    product_id: UUID
    embedding: List[float]
    embedding_type: str = "semantic"
    model_version: str = "gemini-2.0-flash-lite"
