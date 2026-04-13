"""
Embedding Generator для парсера.
"""
import logging
from typing import Dict, List

from estet_shared.ai_clients.embedding_generator import EmbeddingGenerator as BaseEmbeddingGenerator
from estet_shared.ai_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class EmbeddingGenerator(BaseEmbeddingGenerator):
    """Расширенный генератор эмбеддингов для парсера"""

    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)

    async def generate_for_product(self, product_data: Dict) -> List[float]:
        """
        Генерирует embedding для продукта.

        Args:
            product_data: Данные продукта

        Returns:
            List[float]: Вектор embedding (768 dimensions)
        """
        return await self.generate_from_product_description(product_data)

    async def generate_batch(self, products: List[Dict]) -> List[List[float]]:
        """
        Генерирует эмбеддинги для батча продуктов.

        Args:
            products: Список продуктов

        Returns:
            List[List[float]]: Список эмбеддингов
        """
        embeddings = []
        for i, product in enumerate(products):
            logger.info(f"🔄 Генерация embedding {i+1}/{len(products)}: {product.get('name', 'Unknown')}")
            try:
                embedding = await self.generate_for_product(product)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"❌ Ошибка генерации embedding для {product.get('name')}: {e}")
                embeddings.append([0.0] * 768)  # Заглушка при ошибке

        return embeddings
