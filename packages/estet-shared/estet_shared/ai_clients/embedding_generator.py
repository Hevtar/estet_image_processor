"""
Embedding generator для ESTET Platform.
"""
import logging
from typing import List

from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Генератор эмбеддингов для продуктов"""

    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def generate_from_text(self, text: str) -> List[float]:
        """
        Генерирует embedding из текста.

        Args:
            text: Текст для генерации embedding

        Returns:
            List[float]: Вектор embedding (768 dimensions)
        """
        return await self.client.generate_embedding(text)

    async def generate_from_product_description(self, product_data: dict) -> List[float]:
        """
        Генерирует embedding из описания продукта.

        Args:
            product_data: Данные продукта

        Returns:
            List[float]: Вектор embedding
        """
        description = (
            f"{product_data.get('name', '')} "
            f"{product_data.get('category', '')} "
            f"{product_data.get('style', '')} "
            f"{product_data.get('color_family', '')} "
            f"{product_data.get('material', '')} "
            f"{product_data.get('ai_semantic_description', '')}"
        ).strip()

        if not description:
            logger.warning("Пустое описание для генерации embedding")
            return await self.client.generate_embedding(product_data.get('name', 'дверь'))

        return await self.generate_from_text(description)
