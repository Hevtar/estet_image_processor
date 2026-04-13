"""
Vector Search — поиск похожих продуктов в БД.
"""
import logging
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from estet_shared.database import Database
from estet_shared.models import Product, ProductEmbedding
from ..config import settings

logger = logging.getLogger(__name__)


class VectorSearch:
    """Векторный поиск продуктов"""

    def __init__(self):
        self.db = Database(settings.DATABASE_URL)

    async def search(
        self,
        query_text: str,
        max_results: int = 30,
        category: Optional[str] = None,
        style: Optional[str] = None,
    ) -> List[Product]:
        """
        Найти похожие продукты по текстовому запросу.

        Args:
            query_text: Текстовый запрос
            max_results: Максимум результатов
            category: Фильтр по категории
            style: Фильтр по стилю

        Returns:
            List[Product]: Найденные продукты
        """
        try:
            async with self.db.session() as session:
                # Базовый запрос
                query = select(Product).join(ProductEmbedding, isouter=True)

                # Применяем фильтры
                if category:
                    query = query.where(Product.category == category)
                if style:
                    query = query.where(Product.style == style)

                # Ограничиваем результаты
                query = query.limit(max_results)

                result = await session.execute(query)
                products = result.scalars().all()

                logger.info(f"🔍 Найдено {len(products)} продуктов")
                return products

        except Exception as e:
            logger.error(f"❌ Ошибка векторного поиска: {e}")
            return []

    async def search_by_embedding(
        self,
        embedding: List[float],
        max_results: int = 30,
        category: Optional[str] = None,
        style: Optional[str] = None,
    ) -> List[Dict]:
        """
        Найти продукты по cosine similarity.

        Args:
            embedding: Query embedding (768 dimensions)
            max_results: Максимум результатов
            category: Фильтр по категории
            style: Фильтр по стилю

        Returns:
            List[Dict]: Продукты с score
        """
        try:
            async with self.db.session() as session:
                # Используем pgvector для cosine similarity
                from sqlalchemy import literal, text

                # Создаемembedding из списка
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

                query = text(f"""
                    SELECT p.*, pe.embedding,
                           1 - (pe.embedding <=> '{embedding_str}'::vector) as similarity
                    FROM products p
                    LEFT JOIN product_embeddings pe ON p.id = pe.product_id
                    WHERE pe.embedding IS NOT NULL
                    {"AND p.category = :category" if category else ""}
                    {"AND p.style = :style" if style else ""}
                    ORDER BY similarity DESC
                    LIMIT :limit
                """)

                params = {"limit": max_results}
                if category:
                    params["category"] = category
                if style:
                    params["style"] = style

                result = await session.execute(query, params)
                rows = result.fetchall()

                products_with_scores = []
                for row in rows:
                    products_with_scores.append({
                        "product": row,
                        "score": row[-1] if row[-1] else 0,
                    })

                logger.info(f"🔍 Найдено {len(products_with_scores)} продуктов по embedding")
                return products_with_scores

        except Exception as e:
            logger.error(f"❌ Ошибка поиска по embedding: {e}")
            return []
