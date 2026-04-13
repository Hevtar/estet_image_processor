"""
URL Discovery — обнаружение и управление URL.
"""
import logging
from typing import List, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class URLDiscovery:
    """Класс для обнаружения и управления URL"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.visited: Set[str] = set()
        self.to_visit: List[str] = []

    def add_url(self, url: str):
        """Добавить URL в очередь"""
        full_url = self._normalize_url(url)
        if full_url and full_url not in self.visited:
            self.to_visit.append(full_url)
            logger.debug(f"➕ Добавлен URL: {full_url}")

    def get_next_url(self) -> str:
        """Получить следующий URL из очереди"""
        if self.to_visit:
            url = self.to_visit.pop(0)
            self.visited.add(url)
            return url
        return None

    def mark_visited(self, url: str):
        """Отметить URL как посещенный"""
        self.visited.add(self._normalize_url(url))

    def is_visited(self, url: str) -> bool:
        """Проверить, посещен ли URL"""
        return self._normalize_url(url) in self.visited

    def clear(self):
        """Очистить очередь и историю"""
        self.visited.clear()
        self.to_visit.clear()

    def _normalize_url(self, url: str) -> str:
        """Нормализовать URL"""
        if url.startswith("/"):
            return urljoin(self.base_url, url)
        return url

    def filter_product_urls(self, urls: List[str]) -> List[str]:
        """
        Отфильтровать только URL продуктов.

        Args:
            urls: Список URL

        Returns:
            List[str]: URL продуктов
        """
        product_patterns = [
            "/product/",
            "/door/",
            "/doors/",
            "/collection/",
        ]

        filtered = []
        for url in urls:
            if any(pattern in url for pattern in product_patterns):
                filtered.append(url)

        logger.info(f"🔍 Отфильтровано {len(filtered)} продуктивных URL из {len(urls)}")
        return filtered

    def filter_collection_urls(self, urls: List[str]) -> List[str]:
        """
        Отфильтровать только URL коллекций.

        Args:
            urls: Список URL

        Returns:
            List[str]: URL коллекций
        """
        collection_patterns = [
            "/kategoriya/",
            "/category/",
            "/collections/",
        ]

        filtered = []
        for url in urls:
            if any(pattern in url for pattern in collection_patterns):
                filtered.append(url)

        logger.info(f"📂 Отфильтровано {len(filtered)} URL коллекций из {len(urls)}")
        return filtered

    @property
    def stats(self) -> dict:
        """Статистика"""
        return {
            "visited": len(self.visited),
            "to_visit": len(self.to_visit),
        }
