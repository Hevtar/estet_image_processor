"""
Ranking Service — multi-factor ранжирование результатов.
"""
import logging
from typing import Dict, List

from estet_shared.models import Product

logger = logging.getLogger(__name__)


class RankingService:
    """Multi-factor ранжирование продуктов"""

    def rank(
        self,
        products: List[Product],
        analysis: Dict,
    ) -> Dict[Product, float]:
        """
        Ранжировать продукты на основе анализа.

        Факторы ранжирования:
        1. Semantic similarity (embedding)
        2. Style match
        3. Color match
        4. Category match
        5. Completeness (есть ли описание, изображение)

        Args:
            products: Список продуктов
            analysis: Результат анализа изображения

        Returns:
            Dict[Product, float]: Продукты с итоговым score
        """
        scored = {}

        recommended_styles = analysis.get("recommended_door_styles", [])
        recommended_colors = analysis.get("recommended_door_colors", [])
        query_description = analysis.get("description", "")

        for product in products:
            score = 0.0

            # 1. Style match (weight: 0.3)
            if product.style in recommended_styles:
                score += 0.3

            # 2. Color match (weight: 0.25)
            if product.color_family in recommended_colors:
                score += 0.25

            # 3. Description similarity (weight: 0.25)
            # TODO: Реализовать через embedding similarity
            # Временно используем простое совпадение ключевых слов
            if product.ai_semantic_description:
                desc_lower = product.ai_semantic_description.lower()
                query_lower = query_description.lower()
                # Простое совпадение ключевых слов
                common_words = set(desc_lower.split()) & set(query_lower.split())
                if common_words:
                    score += 0.25 * min(len(common_words) / 10, 1.0)

            # 4. Completeness (weight: 0.1)
            completeness_score = 0.0
            if product.ai_semantic_description:
                completeness_score += 0.05
            if product.main_image_url:
                completeness_score += 0.03
            if product.material and product.material != "Не указан":
                completeness_score += 0.02
            score += completeness_score

            # 5. Price factor (weight: 0.1)
            # TODO: Добавить логику ценового ранжирования
            if product.price:
                score += 0.1

            scored[product] = round(score, 4)

        # Сортируем по score
        sorted_products = dict(
            sorted(scored.items(), key=lambda item: item[1], reverse=True)
        )

        logger.info(f"📊 Ранжировано {len(sorted_products)} продуктов")
        return sorted_products
