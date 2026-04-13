"""
SQLAlchemy и Pydantic модели для продуктов.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DECIMAL, ARRAY, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


# ========================================
# SQLAlchemy ORM Models
# ========================================

class Collection(Base):
    """Коллекция продуктов"""
    __tablename__ = "collections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    url = Column(String(500))
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="collection")


class Product(Base):
    """Продукт в каталоге"""
    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    collection_id = Column(PGUUID(as_uuid=True), ForeignKey("collections.id", ondelete="SET NULL"))

    # Основные данные
    name = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False, unique=True)
    category = Column(String(100), nullable=False)

    # Описания
    original_description = Column(Text)
    ai_semantic_description = Column(Text)

    # Характеристики
    style = Column(String(100))
    color_family = Column(String(50))
    material = Column(String(255))
    finish_type = Column(String(100))
    special_features = Column(ARRAY(Text))

    # URLs
    product_url = Column(String(500), nullable=False)
    main_image_url = Column(String(500))

    # Мета-данные
    price = Column(DECIMAL(10, 2))
    available_sizes = Column(ARRAY(Text))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime)

    # Relationships
    collection = relationship("Collection", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    embeddings = relationship("ProductEmbedding", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    """Изображение продукта"""
    __tablename__ = "product_images"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))

    original_url = Column(String(500), nullable=False)
    local_path = Column(String(500))
    image_hash = Column(String(64))

    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    width = Column(Integer)
    height = Column(Integer)
    size_bytes = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="images")


# ========================================
# Pydantic Schemas
# ========================================

class ProductBase(BaseModel):
    """Базовая схема продукта"""
    name: str
    category: str
    style: Optional[str] = None
    color_family: Optional[str] = None
    material: Optional[str] = None
    product_url: str


class ProductCreate(ProductBase):
    """Схема для создания продукта"""
    collection_id: Optional[UUID] = None
    slug: str
    original_description: Optional[str] = None
    ai_semantic_description: Optional[str] = None
    finish_type: Optional[str] = None
    special_features: List[str] = Field(default_factory=list)
    main_image_url: Optional[str] = None
    price: Optional[float] = None
    available_sizes: List[str] = Field(default_factory=list)


class ProductResponse(ProductBase):
    """Схема ответа с продуктом"""
    id: UUID
    collection_id: Optional[UUID]
    slug: str
    ai_semantic_description: Optional[str]
    main_image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
