"""
Scraper — извлечение данных из HTML через BeautifulSoup.
"""
import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from ..config import settings

logger = logging.getLogger(__name__)


class Scraper:
    """Scraper для извлечения данных из HTML"""

    def __init__(self):
        self.base_url = settings.ESTET_BASE_URL

    def parse_product_page(self, html: str) -> Dict:
        """
        Парсит страницу продукта.

        Args:
            html: HTML контент страницы

        Returns:
            Dict: Данные продукта
        """
        soup = BeautifulSoup(html, "html.parser")

        product_data = {
            "name": self._extract_name(soup),
            "category": self._extract_category(soup),
            "style": self._extract_style(soup),
            "color_family": self._extract_color(soup),
            "material": self._extract_material(soup),
            "finish_type": self._extract_finish_type(soup),
            "price": self._extract_price(soup),
            "description": self._extract_description(soup),
            "image_urls": self._extract_image_urls(soup),
            "available_sizes": self._extract_sizes(soup),
            "special_features": self._extract_special_features(soup),
        }

        logger.info(f"📦 Спаршен продукт: {product_data['name']}")
        return product_data

    def parse_collection_page(self, html: str) -> List[str]:
        """
        Парсит страницу коллекции и возвращает ссылки на продукты.

        Args:
            html: HTML контент страницы коллекции

        Returns:
            List[str]: URL продуктов
        """
        soup = BeautifulSoup(html, "html.parser")
        product_urls = []

        # Ищем ссылки на продукты (типичные селекторы для каталога)
        selectors = [
            "a.product-card",
            "a.catalog-item",
            ".products-list a",
            ".catalog-grid a",
            "a[href*='/product/']",
            "a[href*='/door/']",
        ]

        for selector in selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get("href", "")
                    if href:
                        from urllib.parse import urljoin
                        product_urls.append(urljoin(self.base_url, href))
                break

        logger.info(f"🔗 Найдено {len(product_urls)} продуктов на странице")
        return list(set(product_urls))  # Убираем дубликаты

    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Извлекает название продукта"""
        selectors = ["h1.product-title", "h1", ".product-name", ".product-title"]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return "Неизвестный продукт"

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Извлекает категорию продукта"""
        selectors = [".product-category", ".category", ".breadcrumb-item:last"]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        # Пытаемся определить из URL
        if "/doors/" in soup.base.get("href", "") if soup.base else "":
            return "Двери межкомнатные"
        return "Другое"

    def _extract_style(self, soup: BeautifulSoup) -> str:
        """Извлекает стиль продукта"""
        text = soup.get_text().lower()

        style_patterns = {
            "неоклассика": ["неоклассик", "neoclassic"],
            "современный": ["современн", "modern", "contemporary"],
            "минимализм": ["минимализм", "minimalism", "минималист"],
            "классика": ["классик", "classic", "классическ"],
            "лофт": ["лофт", "loft"],
            "скандинавский": ["скандинавск", "scandi"],
            "арт-деко": ["арт-деко", "art deco", "art-deco"],
        }

        for style, patterns in style_patterns.items():
            if any(p in text for p in patterns):
                return style

        return "unknown"

    def _extract_color(self, soup: BeautifulSoup) -> str:
        """Извлекает цвет продукта"""
        text = soup.get_text().lower()

        color_patterns = {
            "белый": ["белый", "белоснежный", "white"],
            "серый": ["серый", "grey", "графит"],
            "коричневый": ["коричневый", "brown", "венге", "орех", "дуб"],
            "черный": ["черный", "black", "чёрный"],
            "бежевый": ["бежевый", "beige", "светлый"],
        }

        for color, patterns in color_patterns.items():
            if any(p in text for p in patterns):
                return color

        return "unknown"

    def _extract_material(self, soup: BeautifulSoup) -> str:
        """Извлекает материал продукта"""
        selectors = [".product-material", ".material", ".specs-table td"]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if "массив" in text.lower():
                    return "Массив"
                elif "шпон" in text.lower():
                    return "Шпон"
                elif "экошпон" in text.lower():
                    return "Экошпон"
                elif "МДФ" in text:
                    return "МДФ"
                return text
        return "Не указан"

    def _extract_finish_type(self, soup: BeautifulSoup) -> str:
        """Извлекает тип отделки"""
        text = soup.get_text().lower()
        if "матов" in text:
            return "матовый"
        elif "глянц" in text:
            return "глянец"
        elif "эмаль" in text:
            return "эмаль"
        return "unknown"

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Извлекает цену"""
        selectors = [".price-value", ".product-price", ".price", ".cost"]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # Извлекаем число из текста
                match = re.search(r"(\d[\d\s]*)", text)
                if match:
                    return float(match.group(1).replace(" ", ""))
        return None

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлекает описание продукта"""
        selectors = [".product-description", ".description", ".product-text", ".full-description"]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""

    def _extract_image_urls(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает URL изображений"""
        image_urls = []
        selectors = [
            ".product-gallery img",
            ".product-images img",
            ".gallery img",
            ".product-photo img",
        ]

        for selector in selectors:
            images = soup.select(selector)
            if images:
                for img in images:
                    src = img.get("src") or img.get("data-src")
                    if src:
                        from urllib.parse import urljoin
                        image_urls.append(urljoin(self.base_url, src))
                break

        return image_urls

    def _extract_sizes(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает доступные размеры"""
        sizes = []
        selectors = [".product-sizes li", ".sizes-list li", ".size-option"]
        for selector in selectors:
            elems = soup.select(selector)
            if elems:
                for elem in elems:
                    sizes.append(elem.get_text(strip=True))
                break
        return sizes

    def _extract_special_features(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает особенности продукта"""
        features = []
        text = soup.get_text().lower()

        feature_keywords = [
            "звукоизоляци",
            "влагостойк",
            "огнестойк",
            "раздвижн",
            "скрывт",
            "телескопич",
        ]

        for keyword in feature_keywords:
            if keyword in text:
                features.append(keyword.capitalize())

        return features
