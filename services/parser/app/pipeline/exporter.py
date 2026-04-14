"""
Exporter — экспорт данных в PostgreSQL и JSON.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from estet_shared.models import Base, Collection, Product, ProductImage, ProductEmbedding
from estet_shared.database import Database

logger = logging.getLogger(__name__)


class Exporter:
    """Экспортер данных в БД"""

    def __init__(self, database: Database):
        self.db = database

    async def export_collection(
        self,
        session: AsyncSession,
        collection_data: Dict,
    ) -> Collection:
        """
        Экспортировать коллекцию.

        Args:
            session: DB сессия
            collection_data: Словарь с данными коллекции:
                {
                    "name": str,
                    "slug": str,
                    "description": str,
                    "url": str,
                    "image_url": str,
                    "features": List[str]  (опционально)
                }

        Returns:
            Collection: Созданная или найденная коллекция
        """
        slug = collection_data.get("slug") or self._generate_slug(
            collection_data.get("name", "")
        )

        if not slug:
            raise ValueError("Невозможно создать коллекцию без slug/name")

        # Проверяем существование
        result = await session.execute(
            select(Collection).where(Collection.slug == slug)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем описание если появилось новое
            if collection_data.get("description") and not existing.description:
                existing.description = collection_data["description"]
                logger.info(f"♻️ Обновлено описание коллекции: {slug}")
            else:
                logger.info(f"♻️ Коллекция уже существует: {slug}")
            return existing

        # Создаем новую
        collection = Collection(
            name=collection_data.get("name", ""),
            slug=slug,
            description=collection_data.get("description", ""),
            url=collection_data.get("url", ""),
            image_url=collection_data.get("image_url", ""),
        )
        session.add(collection)
        await session.flush()

        logger.info(f"✅ Создана коллекция: {collection_data.get('name')}")
        return collection

    async def export_product_images(
        self,
        session: AsyncSession,
        product_id: UUID,
        image_paths: List[str],
        image_urls: Optional[List[str]] = None,
    ) -> List[ProductImage]:
        """
        Пакетное сохранение изображений продукта.

        Args:
            session: DB сессия
            product_id: ID продукта
            image_paths: Локальные пути к файлам
            image_urls: Оригинальные URL (опционально)

        Returns:
            List[ProductImage]: Список созданных записей
        """
        saved = []

        for i, local_path in enumerate(image_paths):
            image_data = {
                "local_path": local_path,
                "url": image_urls[i] if image_urls and i < len(image_urls) else "",
                "is_primary": (i == 0),  # Первое изображение — главное
                "order": i,
            }

            try:
                img = await self.export_product_image(session, product_id, image_data)
                saved.append(img)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось сохранить изображение {local_path}: {e}")

        logger.info(f"🖼️ Сохранено {len(saved)} изображений для продукта {product_id}")
        return saved

    async def export_product(
        self,
        session: AsyncSession,
        product_data: Dict,
        collection_id: Optional[UUID] = None
    ) -> Product:
        """
        Экспортировать продукт.

        Args:
            session: DB сессия
            product_data: Данные продукта
            collection_id: ID коллекции

        Returns:
            Product: Созданный или обновленный продукт
        """
        slug = self._generate_slug(product_data.get("name", ""))

        # Проверяем существование
        result = await session.execute(select(Product).where(Product.slug == slug))
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем
            self._update_product(existing, product_data, collection_id)
            logger.info(f"♻️ Обновлен продукт: {product_data.get('name')}")
            return existing

        # Создаем новый
        product = Product(
            collection_id=collection_id,
            name=product_data.get("name", ""),
            slug=slug,
            category=product_data.get("category", "Другое"),
            original_description=product_data.get("original_description", ""),
            ai_semantic_description=product_data.get("ai_semantic_description", ""),
            style=product_data.get("style", "unknown"),
            color_family=product_data.get("color_family", "unknown"),
            material=product_data.get("material", "Не указан"),
            finish_type=product_data.get("finish_type", "unknown"),
            special_features=product_data.get("special_features", []),
            product_url=product_data.get("product_url", ""),
            main_image_url=product_data.get("main_image_url", ""),
            price=product_data.get("price"),
            available_sizes=product_data.get("available_sizes", []),
            last_scraped_at=datetime.utcnow(),
        )
        session.add(product)
        await session.flush()

        logger.info(f"✅ Создан продукт: {product_data.get('name')}")
        return product

    async def export_product_image(
        self,
        session: AsyncSession,
        product_id: UUID,
        image_data: Dict
    ) -> ProductImage:
        """
        Экспортировать изображение продукта.

        Args:
            session: DB сессия
            product_id: ID продукта
            image_data: Данные изображения

        Returns:
            ProductImage: Созданное изображение
        """
        image = ProductImage(
            product_id=product_id,
            original_url=image_data.get("url", ""),
            local_path=image_data.get("local_path"),
            image_hash=image_data.get("hash"),
            is_primary=image_data.get("is_primary", False),
            display_order=image_data.get("order", 0),
            width=image_data.get("width"),
            height=image_data.get("height"),
            size_bytes=image_data.get("size_bytes"),
        )
        session.add(image)
        await session.flush()

        return image

    async def export_embedding(
        self,
        session: AsyncSession,
        product_id: UUID,
        embedding: List[float],
        embedding_type: str = "semantic",
        model_version: str = "gemini-2.0-flash-lite"
    ) -> ProductEmbedding:
        """
        Экспортировать embedding.

        Args:
            session: DB сессия
            product_id: ID продукта
            embedding: Вектор embedding
            embedding_type: Тип embedding
            model_version: Версия модели

        Returns:
            ProductEmbedding: Созданный embedding
        """
        emb = ProductEmbedding(
            product_id=product_id,
            embedding=embedding,
            embedding_type=embedding_type,
            model_version=model_version,
        )
        session.add(emb)
        await session.flush()

        return emb

    def export_to_json(self, products: List[Dict], filepath: str):
        """
        Экспортировать в JSON файл.

        Args:
            products: Список продуктов
            filepath: Путь к файлу
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Экспортировано {len(products)} продуктов в {filepath}")

    def _generate_slug(self, name: str) -> str:
        """Генерирует slug из названия"""
        import re
        slug = name.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_-]+", "-", slug)
        slug = slug.strip("-")
        return slug

    def _update_product(self, product: Product, data: Dict, collection_id: Optional[UUID]):
        """Обновить продукт"""
        for key, value in data.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        product.last_scraped_at = datetime.utcnow()
