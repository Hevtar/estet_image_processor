"""
Deduplicator — удаление дубликатов продуктов.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class Deduplicator:
    """Дедупликатор продуктов"""

    def deduplicate_by_url(self, products: List[Dict]) -> List[Dict]:
        """
        Удалить дубликаты по URL.

        Args:
            products: Список продуктов

        Returns:
            List[Dict]: Уникальные продукты
        """
        seen_urls = set()
        unique = []

        for product in products:
            url = product.get("product_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(product)
            else:
                logger.debug(f"🔄 Дубликат URL: {url}")

        removed = len(products) - len(unique)
        if removed > 0:
            logger.info(f"🧹 Удалено {removed} дубликатов по URL")

        return unique

    def deduplicate_by_name(self, products: List[Dict]) -> List[Dict]:
        """
        Удалить дубликаты по названию.

        Args:
            products: Список продуктов

        Returns:
            List[Dict]: Уникальные продукты
        """
        seen_names = set()
        unique = []

        for product in products:
            name = product.get("name", "").lower()
            if name and name not in seen_names:
                seen_names.add(name)
                unique.append(product)
            else:
                logger.debug(f"🔄 Дубликат имени: {name}")

        removed = len(products) - len(unique)
        if removed > 0:
            logger.info(f"🧹 Удалено {removed} дубликатов по имени")

        return unique

    def deduplicate(self, products: List[Dict]) -> List[Dict]:
        """
        Полная дедупликация (по URL и имени).

        Args:
            products: Список продуктов

        Returns:
            List[Dict]: Уникальные продукты
        """
        # Сначала по URL
        unique_by_url = self.deduplicate_by_url(products)
        # Потом по имени
        unique_by_name = self.deduplicate_by_name(unique_by_url)

        return unique_by_name
